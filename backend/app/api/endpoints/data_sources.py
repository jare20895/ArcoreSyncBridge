from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

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
from app.services.introspection import PostgresIntrospector, build_dsn

router = APIRouter()


def _serialize_tables(db: Session, database_id: UUID) -> List[DatabaseTableRead]:
    stmt = (
        select(DatabaseTable, func.count(TableColumn.id).label("columns_count"))
        .outerjoin(TableColumn, TableColumn.table_id == DatabaseTable.id)
        .where(DatabaseTable.database_id == database_id)
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


@router.get("/tables", response_model=List[DatabaseTableRead])
def list_tables(
    database_id: UUID = Query(..., description="Logical database ID"),
    db: Session = Depends(get_db),
):
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return _serialize_tables(db, database_id)


@router.post("/tables/extract", response_model=List[DatabaseTableRead])
def extract_table_inventory(
    request: TableInventoryExtractRequest,
    db: Session = Depends(get_db),
):
    instance = db.get(DatabaseInstance, request.instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    database = db.get(Database, request.database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    run = IntrospectionRun(database_instance_id=instance.id, status="RUNNING")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        dsn = build_dsn(instance, database.database_name)
        introspector = PostgresIntrospector(dsn)
        inventory = introspector.get_table_inventory(request.schema)

        created = 0
        updated = 0

        for table in inventory:
            existing = (
                db.query(DatabaseTable)
                .filter_by(
                    database_id=request.database_id,
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
                        database_id=request.database_id,
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
            "schema": request.schema,
        }
        db.commit()
    except Exception as e:
        db.rollback()
        run = db.get(IntrospectionRun, run.id)
        if run:
            run.status = "FAILED"
            run.ended_at = datetime.utcnow()
            run.stats = {"error": str(e), "schema": request.schema}
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return _serialize_tables(db, request.database_id)


@router.post("/tables/extract-details")
def extract_table_details(
    request: TableDetailsExtractRequest,
    db: Session = Depends(get_db),
):
    instance = db.get(DatabaseInstance, request.instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    tables = (
        db.query(DatabaseTable)
        .filter(DatabaseTable.id.in_(request.table_ids))
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

    return {"tables_processed": processed}


@router.get("/tables/{table_id}", response_model=DatabaseTableDetailRead)
def get_table_details(
    table_id: UUID,
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

    return DatabaseTableDetailRead(
        table=table_read,
        columns=[TableColumnRead.model_validate(col) for col in columns],
        constraints=[TableConstraintRead.model_validate(c) for c in constraints],
        indexes=[TableIndexRead.model_validate(idx) for idx in indexes],
    )
