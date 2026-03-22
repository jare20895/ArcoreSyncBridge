from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.api.responses import success_response
from app.core.security import EDITOR_ROLES, OPERATOR_ROLES, VIEWER_ROLES, Principal, require_roles
from app.db.base import Base
# In a real app, we would use a get_db dependency
# For now, I'll mock the DB session or create a basic one if needed.
# Since I haven't set up the full dependency injection for DB yet, I will create a temporary one.

from app.models.core import DatabaseInstance
from app.schemas.database_instance import (
    DatabaseInstanceCreate,
    DatabaseInstanceRead,
    DatabaseInstanceUpdate,
    ConnectionTestResult,
    ConnectionTestRequest
)
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.introspection import SchemaSnapshot
from app.services.introspection import introspect_database
from app.services.audit import record_audit_event
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=ApiResponse[DatabaseInstanceRead], status_code=status.HTTP_201_CREATED)
def create_database_instance(
    instance: DatabaseInstanceCreate,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    db_instance = DatabaseInstance(**instance.model_dump())
    try:
        db.add(db_instance)
        db.commit()
        db.refresh(db_instance)
        record_audit_event(
            db,
            request,
            principal,
            action="database_instance.create",
            resource_type="database_instance",
            resource_id=str(db_instance.id),
            details=instance.model_dump(exclude={"password"}),
        )
        return success_response(request, db_instance)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[List[DatabaseInstanceRead]])
def list_database_instances(
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    database_id: Optional[UUID] = Query(None),
    q: Optional[str] = Query(None, description="Search by instance label, host, or database name"),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(DatabaseInstance)
    if database_id:
        query = query.filter(DatabaseInstance.database_id == database_id)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            DatabaseInstance.instance_label.ilike(search)
            | DatabaseInstance.host.ilike(search)
            | DatabaseInstance.db_name.ilike(search)
        )
    if role:
        query = query.filter(DatabaseInstance.role == role)
    if status:
        query = query.filter(DatabaseInstance.status == status)

    total = query.count()
    instances = query.order_by(DatabaseInstance.instance_label).offset(offset).limit(limit).all()
    return success_response(request, instances, meta={"total": total, "limit": limit, "offset": offset})

@router.get("/{instance_id}", response_model=ApiResponse[DatabaseInstanceRead])
def get_database_instance(
    instance_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
    return success_response(request, db_instance)

@router.put("/{instance_id}", response_model=ApiResponse[DatabaseInstanceRead])
def update_database_instance(
    instance_id: UUID,
    instance_update: DatabaseInstanceUpdate,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
    
    update_data = instance_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_instance, key, value)
    
    try:
        db.commit()
        db.refresh(db_instance)
        record_audit_event(
            db,
            request,
            principal,
            action="database_instance.update",
            resource_type="database_instance",
            resource_id=str(db_instance.id),
            details=update_data,
        )
        return success_response(request, db_instance)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{instance_id}", response_model=ApiResponse[MessageResponse])
def delete_database_instance(
    instance_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    db.delete(db_instance)
    db.commit()
    record_audit_event(
        db,
        request,
        principal,
        action="database_instance.delete",
        resource_type="database_instance",
        resource_id=str(instance_id),
        details={"instance_label": db_instance.instance_label},
    )
    return success_response(request, {"message": "Database instance deleted"})

@router.post("/test-connection", response_model=ConnectionTestResult)
def test_connection_raw(
    connection: ConnectionTestRequest,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
):
    """
    Test database connection with provided credentials (before creating instance).
    """
    import psycopg2
    try:
        # Attempt to connect to the database
        conn = psycopg2.connect(
            host=connection.host,
            port=connection.port,
            database=connection.db_name,
            user=connection.username,
            password=connection.password,
            connect_timeout=5
        )
        conn.close()
        return ConnectionTestResult(success=True, message="Connection successful!")
    except psycopg2.OperationalError as e:
        return ConnectionTestResult(success=False, message=f"Connection failed: {str(e)}")
    except Exception as e:
        return ConnectionTestResult(success=False, message=f"Unexpected error: {str(e)}")

@router.post("/{instance_id}/test-connection", response_model=ConnectionTestResult)
def test_connection(
    instance_id: UUID,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Test database connection using stored credentials from the instance.
    """
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    # Check if we have all required credentials
    if not db_instance.db_name or not db_instance.username or not db_instance.password:
        return ConnectionTestResult(
            success=False,
            message="Missing database name, username, or password in stored instance"
        )

    import psycopg2
    try:
        # Attempt to connect using stored credentials
        conn = psycopg2.connect(
            host=db_instance.host,
            port=db_instance.port,
            database=db_instance.db_name,
            user=db_instance.username,
            password=db_instance.password,
            connect_timeout=5
        )
        conn.close()
        return ConnectionTestResult(success=True, message="Connection successful (using stored credentials)")
    except psycopg2.OperationalError as e:
        return ConnectionTestResult(success=False, message=f"Connection failed: {str(e)}")
    except Exception as e:
        return ConnectionTestResult(success=False, message=f"Unexpected error: {str(e)}")

@router.get("/{instance_id}/schema", response_model=SchemaSnapshot)
def get_instance_schema(
    instance_id: UUID,
    schema: str = "public",
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
        
    try:
        return introspect_database(db_instance, schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
