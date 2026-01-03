"""
API endpoints for Database CRUD operations.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inventory import Database
from app.schemas.database import DatabaseCreate, DatabaseUpdate, DatabaseResponse

router = APIRouter()


@router.get("/", response_model=List[DatabaseResponse])
def list_databases(
    application_id: Optional[UUID] = Query(None, description="Filter by application ID"),
    db: Session = Depends(get_db)
):
    """List all databases, optionally filtered by application."""
    query = db.query(Database)

    if application_id:
        query = query.filter(Database.application_id == application_id)

    databases = query.order_by(Database.name).all()
    return databases


@router.get("/{database_id}", response_model=DatabaseResponse)
def get_database(database_id: UUID, db: Session = Depends(get_db)):
    """Get a specific database by ID."""
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return database


@router.post("/", response_model=DatabaseResponse, status_code=201)
def create_database(database_data: DatabaseCreate, db: Session = Depends(get_db)):
    """Create a new database."""
    database = Database(**database_data.model_dump())
    db.add(database)
    db.commit()
    db.refresh(database)
    return database


@router.put("/{database_id}", response_model=DatabaseResponse)
def update_database(
    database_id: UUID,
    database_data: DatabaseUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing database."""
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Update only provided fields
    update_data = database_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(database, field, value)

    db.commit()
    db.refresh(database)
    return database


@router.delete("/{database_id}", status_code=204)
def delete_database(database_id: UUID, db: Session = Depends(get_db)):
    """Delete a database."""
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    db.delete(database)
    db.commit()
    return None
