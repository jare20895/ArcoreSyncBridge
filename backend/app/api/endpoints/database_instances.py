from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, text

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
from app.schemas.introspection import SchemaSnapshot
from app.services.introspection import introspect_database
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=DatabaseInstanceRead, status_code=status.HTTP_201_CREATED)
def create_database_instance(
    instance: DatabaseInstanceCreate,
    db: Session = Depends(get_db)
):
    db_instance = DatabaseInstance(**instance.model_dump())
    try:
        db.add(db_instance)
        db.commit()
        db.refresh(db_instance)
        return db_instance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DatabaseInstanceRead])
def list_database_instances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stmt = select(DatabaseInstance).offset(skip).limit(limit)
    result = db.execute(stmt)
    return result.scalars().all()

@router.get("/{instance_id}", response_model=DatabaseInstanceRead)
def get_database_instance(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
    return db_instance

@router.put("/{instance_id}", response_model=DatabaseInstanceRead)
def update_database_instance(
    instance_id: UUID,
    instance_update: DatabaseInstanceUpdate,
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
        return db_instance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_database_instance(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    db.delete(db_instance)
    db.commit()
    return None

@router.post("/test-connection", response_model=ConnectionTestResult)
def test_connection_raw(
    connection: ConnectionTestRequest
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
    db: Session = Depends(get_db)
):
    """
    Test database connection using stored credentials from the instance.
    """
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    # Check if we have all required credentials
    if not db_instance.db_name or not db_instance.username:
        return ConnectionTestResult(
            success=False,
            message="Missing database name or username in stored instance"
        )

    import psycopg2
    try:
        # Attempt to connect using stored credentials
        conn = psycopg2.connect(
            host=db_instance.host,
            port=db_instance.port,
            database=db_instance.db_name,
            user=db_instance.username,
            password=db_instance.password or "",
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
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")
        
    try:
        return introspect_database(db_instance, schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
