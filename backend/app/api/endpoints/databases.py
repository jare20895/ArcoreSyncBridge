"""
API endpoints for Database CRUD operations.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.db.session import get_db
from app.models.inventory import Database
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.database import DatabaseCreate, DatabaseUpdate, DatabaseResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[List[DatabaseResponse]])
def list_databases(
    request: Request,
    application_id: Optional[UUID] = Query(None, description="Filter by application ID"),
    db: Session = Depends(get_db)
):
    """List all databases, optionally filtered by application."""
    query = db.query(Database)

    if application_id:
        query = query.filter(Database.application_id == application_id)

    databases = query.order_by(Database.name).all()
    return success_response(request, databases)


@router.get("/{database_id}", response_model=ApiResponse[DatabaseResponse])
def get_database(database_id: UUID, request: Request, db: Session = Depends(get_db)):
    """Get a specific database by ID."""
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return success_response(request, database)


@router.post("/", response_model=ApiResponse[DatabaseResponse], status_code=201)
def create_database(database_data: DatabaseCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new database."""
    database = Database(**database_data.model_dump())
    db.add(database)
    db.commit()
    db.refresh(database)
    return success_response(request, database)


@router.put("/{database_id}", response_model=ApiResponse[DatabaseResponse])
def update_database(
    database_id: UUID,
    database_data: DatabaseUpdate,
    request: Request,
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
    return success_response(request, database)


@router.delete("/{database_id}", response_model=ApiResponse[MessageResponse])
def delete_database(database_id: UUID, request: Request, db: Session = Depends(get_db)):
    """Delete a database."""
    database = db.get(Database, database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    db.delete(database)
    db.commit()
    return success_response(request, {"message": "Database deleted"})
