from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.responses import success_response
from app.models.core import SharePointConnection
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.sharepoint_connection import (
    SharePointConnectionCreate,
    SharePointConnectionRead,
    SharePointConnectionUpdate
)
from app.api.endpoints.database_instances import get_db # Reusing dependency for now

router = APIRouter()

@router.post("/", response_model=ApiResponse[SharePointConnectionRead], status_code=status.HTTP_201_CREATED)
def create_connection(
    connection: SharePointConnectionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    db_conn = SharePointConnection(**connection.model_dump())
    try:
        db.add(db_conn)
        db.commit()
        db.refresh(db_conn)
        return success_response(request, db_conn)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[List[SharePointConnectionRead]])
def list_connections(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stmt = select(SharePointConnection).offset(skip).limit(limit)
    result = db.execute(stmt)
    return success_response(request, result.scalars().all())

@router.get("/{connection_id}", response_model=ApiResponse[SharePointConnectionRead])
def get_connection(
    connection_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    db_conn = db.get(SharePointConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return success_response(request, db_conn)

@router.put("/{connection_id}", response_model=ApiResponse[SharePointConnectionRead])
def update_connection(
    connection_id: UUID,
    connection_update: SharePointConnectionUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    db_conn = db.get(SharePointConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    update_data = connection_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_conn, key, value)
    
    try:
        db.commit()
        db.refresh(db_conn)
        return success_response(request, db_conn)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{connection_id}", response_model=ApiResponse[MessageResponse])
def delete_connection(
    connection_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    db_conn = db.get(SharePointConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(db_conn)
    db.commit()
    return success_response(request, {"message": "Connection deleted"})
