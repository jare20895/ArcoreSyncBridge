from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.security import OPERATOR_ROLES, VIEWER_ROLES, Principal, require_roles
from app.db.session import get_db
from app.models.core import DatabaseInstance
from app.models.inventory import (
    Database,
    DatabaseTable,
    TableColumn,
    TableConstraint,
    TableIndex,
    SchemaSnapshot,
    IntrospectionRun,
)
from app.schemas.catalog import (
    TableInventoryExtractRequest,
    TableDetailsExtractRequest,
    DatabaseTableRead,
    DatabaseTableDetailRead,
    TableColumnRead,
    TableConstraintRead,
    TableIndexRead,
)
from app.schemas.api import ApiResponse
from app.services.audit import record_audit_event
from app.services.introspection import PostgresIntrospector, build_dsn

router = APIRouter()


def _serialize_tables(query):
    stmt = (
        query.with_entities(DatabaseTable, func.count(TableColumn.id).label("columns_count"))
        .outerjoin(TableColumn, TableColumn.table_id == DatabaseTable.id)
        .group_by(DatabaseTable.id)
        .order_by(DatabaseTable.schema_name, DatabaseTable.table_name)
    )
    results = db.execute(stmt).all()
    tables = []
    for table, columns_count in results:
        tables.append(
            DatabaseTableRead(
                id=table.id,
                database_id=table.database_id,
                schema_name=table.schema_name,
                table_name=table.table_name,
                table_type=table.table_type,
                primary_key=table.primary_key,
                row_estimate=table.row_estimate,
                last_introspected_at=table.last_introspected_at,
                columns_count=int(columns_count or 0),
            )
        )
    return tables


@router.get("/tables", response_model=ApiResponse[List[DatabaseTableRead]])
def list_tables(
    request: Request,
    database_id: UUID = Query(..., description="Logical database ID"),
    q: str | None = Query(None, description="Search by table or schema"),
    schema_name: str | None = Query(None, description="Filter by schema"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    query = db.query(DatabaseTable).filter(DatabaseTable.database_id == database_id)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            DatabaseTable.table_name.ilike(search)
            | DatabaseTable.schema_name.ilike(search)
        )
    if schema_name:
        query = query.filter(DatabaseTable.schema_name == schema_name)

    total = query.count()
    rows = _serialize_tables(query.offset(offset).limit(limit))
    return success_response(request, rows, meta={"total": total, "limit": limit, "offset": offset})


@router.post("/tables/extract", response_model=ApiResponse[List[DatabaseTableRead]])
def extract_table_inventory(
    payload: TableInventoryExtractRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    instance = db.get(DatabaseInstance, payload.instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    database = db.get(Database, payload.database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    run = IntrospectionRun(database_instance_id=instance.id, status="RUNNING")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        dsn = build_dsn(instance, database.database_name)
        introspector = PostgresIntrospector(dsn)
        inventory = introspector.get_table_inventory(payload.schema_name)

        created = 0
        updated = 0

        for table in inventory:
            existing = (
                db.query(DatabaseTable)
                .filter_by(
                    database_id=payload.database_id,
                    schema_name=table["schema_name"],
                    table_name=table["table_name"],
                )
                .one_or_none()
            )
            if existing:
                existing.table_type = table["table_type"]
                existing.row_estimate = table["row_estimate"]
                updated += 1
            else:
                db.add(
                    DatabaseTable(
                        database_id=payload.database_id,
                        schema_name=table["schema_name"],
                        table_name=table["table_name"],
                        table_type=table["table_type"],
                        row_estimate=table["row_estimate"],
                    )
                )
                created += 1

        run.status = "SUCCESS"
        run.ended_at = datetime.utcnow()
        run.stats = {
            "tables_found": len(inventory),
            "tables_created": created,
            "tables_updated": updated,
            "schema": payload.schema_name,
        }
        db.commit()
    except Exception as e:
        db.rollback()
        run = db.get(IntrospectionRun, run.id)
        if run:
            run.status = "FAILED"
            run.ended_at = datetime.utcnow()
            run.stats = {"error": str(e), "schema": payload.schema_name}
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    result = _serialize_tables(db.query(DatabaseTable).filter(DatabaseTable.database_id == payload.database_id))
    record_audit_event(
        db,
        request,
        principal,
        action="inventory.tables.extract",
        resource_type="database",
        resource_id=str(payload.database_id),
        details={"instance_id": str(payload.instance_id), "schema": payload.schema_name, "table_count": len(result)},
    )
    return success_response(request, result)


@router.post("/tables/extract-details", response_model=ApiResponse[dict])
def extract_table_details(
    payload: TableDetailsExtractRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    instance = db.get(DatabaseInstance, payload.instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    tables = (
        db.query(DatabaseTable)
        .filter(DatabaseTable.id.in_(payload.table_ids))
        .all()
    )
    if not tables:
        raise HTTPException(status_code=404, detail="No matching tables found")

    run = IntrospectionRun(database_instance_id=instance.id, status="RUNNING")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        database_name = None
        database = db.get(Database, tables[0].database_id)
        if database:
            database_name = database.database_name
        dsn = build_dsn(instance, database_name)
        introspector = PostgresIntrospector(dsn)
        processed = 0

        for table in tables:
            details = introspector.get_table_details(table.schema_name, table.table_name)

            db.query(TableColumn).filter(TableColumn.table_id == table.id).delete(synchronize_session=False)
            db.query(TableConstraint).filter(TableConstraint.table_id == table.id).delete(synchronize_session=False)
            db.query(TableIndex).filter(TableIndex.table_id == table.id).delete(synchronize_session=False)

            primary_key_columns = []
            for constraint in details["constraints"]:
                if constraint["constraint_type"] == "PRIMARY_KEY":
                    primary_key_columns.extend(constraint["columns"])
                db.add(
                    TableConstraint(
                        table_id=table.id,
                        constraint_name=constraint["constraint_name"],
                        constraint_type=constraint["constraint_type"],
                        columns=constraint["columns"],
                        referenced_table=constraint["referenced_table"],
                        definition=constraint["definition"],
                    )
                )

            for column in details["columns"]:
                db.add(
                    TableColumn(
                        table_id=table.id,
                        ordinal_position=column["ordinal_position"],
                        column_name=column["column_name"],
                        data_type=column["data_type"],
                        is_nullable=column["is_nullable"],
                        default_value=column["default_value"],
                        is_identity=column["is_identity"],
                        is_primary_key=column["is_primary_key"],
                        is_unique=column["is_unique"],
                    )
                )

            for index in details["indexes"]:
                db.add(
                    TableIndex(
                        table_id=table.id,
                        index_name=index["index_name"],
                        is_unique=index["is_unique"],
                        index_method=index["index_method"],
                        columns=index["columns"],
                        definition=index["definition"],
                    )
                )

            table.primary_key = ", ".join(primary_key_columns) if primary_key_columns else None
            table.last_introspected_at = datetime.utcnow()

            db.add(
                SchemaSnapshot(
                    table_id=table.id,
                    database_instance_id=instance.id,
                    columns=details["columns"],
                    constraints=details["constraints"],
                    indexes=details["indexes"],
                )
            )

            processed += 1

        run.status = "SUCCESS"
        run.ended_at = datetime.utcnow()
        run.stats = {
            "tables_processed": processed,
            "table_ids": [str(t.id) for t in tables],
        }
        db.commit()
    except Exception as e:
        db.rollback()
        run = db.get(IntrospectionRun, run.id)
        if run:
            run.status = "FAILED"
            run.ended_at = datetime.utcnow()
            run.stats = {"error": str(e)}
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    result = {"tables_processed": processed}
    record_audit_event(
        db,
        request,
        principal,
        action="inventory.table_details.extract",
        resource_type="database_instance",
        resource_id=str(payload.instance_id),
        details={"table_ids": [str(table_id) for table_id in payload.table_ids], "tables_processed": processed},
    )
    return success_response(request, result)


@router.get("/tables/{table_id}", response_model=ApiResponse[DatabaseTableDetailRead])
def get_table_details(
    table_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    table = db.get(DatabaseTable, table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    columns = (
        db.query(TableColumn)
        .filter(TableColumn.table_id == table_id)
        .order_by(TableColumn.ordinal_position)
        .all()
    )
    constraints = (
        db.query(TableConstraint)
        .filter(TableConstraint.table_id == table_id)
        .order_by(TableConstraint.constraint_name)
        .all()
    )
    indexes = (
        db.query(TableIndex)
        .filter(TableIndex.table_id == table_id)
        .order_by(TableIndex.index_name)
        .all()
    )

    table_read = DatabaseTableRead(
        id=table.id,
        database_id=table.database_id,
        schema_name=table.schema_name,
        table_name=table.table_name,
        table_type=table.table_type,
        primary_key=table.primary_key,
        row_estimate=table.row_estimate,
        last_introspected_at=table.last_introspected_at,
        columns_count=len(columns),
    )

    return success_response(request, DatabaseTableDetailRead(
        table=table_read,
        columns=[TableColumnRead.model_validate(col) for col in columns],
        constraints=[TableConstraintRead.model_validate(c) for c in constraints],
        indexes=[TableIndexRead.model_validate(idx) for idx in indexes],
    ))
