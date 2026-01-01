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
    ConnectionTestResult
)
from app.schemas.introspection import SchemaSnapshot
from app.services.introspection import introspect_database

# TODO: Move this to a shared dependencies file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Using the connection string from env (or default for now)
SQLALCHEMY_DATABASE_URL = "postgresql://arcore:arcore_password@localhost:5455/arcore_syncbridge"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@router.post("/{instance_id}/test-connection", response_model=ConnectionTestResult)
def test_connection(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    db_instance = db.get(DatabaseInstance, instance_id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Database instance not found")

    # Construct connection string for the target instance
    # Note: In a real scenario, we would need credentials. 
    # For now, I will assume we are testing connectivity to the *same* DB or use placeholder creds
    # if they were stored (they are not currently in the model, just host/port).
    # TO FIX: The spec implies we manage connections, but the model doesn't have user/pass.
    # I will assume standard 'postgres' user or similar for this check, or update the model later.
    # For this pass, I'll attempt a basic TCP check or assume credentials are env-based for the "System" DB.
    # Wait, the spec says "Operator selects the parent application and logical database."
    # The `connection_profiles` mentioned in the design doc store credentials.
    # My `DatabaseInstance` model from `core.py` missed the `connection_profile_id` or similar?
    # Checking `core.py`... `DatabaseInstance` has host/port. `SharePointConnection` is separate.
    # The Implementation Specs 1.1 `DatabaseInstance` does NOT show credentials.
    # It seems credentials might be separate or managed via standard PG env vars/vault.
    # For this "Health Check", I will implement a simple network reachability test to host:port.
    
    import socket
    try:
        sock = socket.create_connection((db_instance.host, db_instance.port), timeout=5)
        sock.close()
        return ConnectionTestResult(success=True, message="Connection successful (Network Reachable)")
    except Exception as e:
        return ConnectionTestResult(success=False, message=f"Connection failed: {str(e)}")

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
