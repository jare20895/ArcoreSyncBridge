from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.core import SharePointConnection
from app.schemas.sharepoint_connection import (
    SharePointConnectionCreate,
    SharePointConnectionRead,
    SharePointConnectionUpdate
)
from app.api.endpoints.database_instances import get_db # Reusing dependency for now

router = APIRouter()

@router.post("/", response_model=SharePointConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    connection: SharePointConnectionCreate,
    db: Session = Depends(get_db)
):
    db_conn = SharePointConnection(**connection.model_dump())
    try:
        db.add(db_conn)
        db.commit()
        db.refresh(db_conn)
        return db_conn
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[SharePointConnectionRead])
def list_connections(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stmt = select(SharePointConnection).offset(skip).limit(limit)
    result = db.execute(stmt)
    return result.scalars().all()

@router.get("/{connection_id}", response_model=SharePointConnectionRead)
def get_connection(
    connection_id: UUID,
    db: Session = Depends(get_db)
):
    db_conn = db.get(SharePointConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return db_conn

@router.put("/{connection_id}", response_model=SharePointConnectionRead)
def update_connection(
    connection_id: UUID,
    connection_update: SharePointConnectionUpdate,
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
        return db_conn
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: UUID,
    db: Session = Depends(get_db)
):
    db_conn = db.get(SharePointConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(db_conn)
    db.commit()
    return None
