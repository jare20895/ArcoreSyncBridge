from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.endpoints.database_instances import get_db
from app.models.core import SyncDefinition, SyncSource, SyncTarget, SyncKeyColumn, FieldMapping
from app.schemas.sync_definition import (
    SyncDefinitionCreate,
    SyncDefinitionRead,
    SyncDefinitionUpdate
)

router = APIRouter()

@router.post("/", response_model=SyncDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_sync_definition(
    def_in: SyncDefinitionCreate,
    db: Session = Depends(get_db)
):
    # 1. Create Parent
    db_def = SyncDefinition(
        name=def_in.name,
        source_table_id=def_in.source_table_id,
        target_list_id=def_in.target_list_id,
        sync_mode=def_in.sync_mode,
        conflict_policy=def_in.conflict_policy,
        key_strategy=def_in.key_strategy,
        key_constraint_name=def_in.key_constraint_name,
        target_strategy=def_in.target_strategy,
        cursor_strategy=def_in.cursor_strategy,
        cursor_column_id=def_in.cursor_column_id,
        sharding_policy=def_in.sharding_policy
    )
    db.add(db_def)
    db.flush() # Generate ID

    # 2. Create Children
    for s in def_in.sources:
        db.add(SyncSource(sync_def_id=db_def.id, **s.model_dump()))
    
    for t in def_in.targets:
        db.add(SyncTarget(sync_def_id=db_def.id, **t.model_dump()))

    for k in def_in.key_columns:
        db.add(SyncKeyColumn(sync_def_id=db_def.id, **k.model_dump()))

    for m in def_in.field_mappings:
        db.add(FieldMapping(sync_def_id=db_def.id, **m.model_dump()))

    try:
        db.commit()
        db.refresh(db_def)
        return db_def
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[SyncDefinitionRead])
def list_sync_definitions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stmt = select(SyncDefinition).offset(skip).limit(limit)
    result = db.execute(stmt)
    return result.scalars().all()

@router.get("/{def_id}", response_model=SyncDefinitionRead)
def get_sync_definition(
    def_id: UUID,
    db: Session = Depends(get_db)
):
    db_def = db.get(SyncDefinition, def_id)
    if not db_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")
    return db_def

@router.put("/{def_id}", response_model=SyncDefinitionRead)
def update_sync_definition(
    def_id: UUID,
    def_in: SyncDefinitionUpdate,
    db: Session = Depends(get_db)
):
    db_def = db.get(SyncDefinition, def_id)
    if not db_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")
    
    update_data = def_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_def, field, value)
    
    db.commit()
    db.refresh(db_def)
    return db_def
