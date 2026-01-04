from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.endpoints.database_instances import get_db
from app.models.core import SyncDefinition, SyncSource, SyncTarget, SyncKeyColumn, FieldMapping
from app.models.inventory import DatabaseTable, TableColumn, SharePointList, SharePointColumn
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

    # 3. Field Mappings - Auto-generation logic
    if def_in.field_mappings:
        # Use provided mappings
        for m in def_in.field_mappings:
            db.add(FieldMapping(sync_def_id=db_def.id, **m.model_dump()))
    elif def_in.source_table_id and def_in.target_list_id:
        # Attempt auto-mapping
        source_cols = db.execute(
            select(TableColumn).where(TableColumn.table_id == def_in.source_table_id)
        ).scalars().all()
        
        target_cols = db.execute(
            select(SharePointColumn).where(SharePointColumn.list_id == def_in.target_list_id)
        ).scalars().all()
        
        # Build lookup for target cols (normalize name)
        target_map = {c.column_name.lower(): c for c in target_cols}
        
        for sc in source_cols:
            sc_norm = sc.column_name.lower()
            if sc_norm in target_map:
                tc = target_map[sc_norm]

                # Phase 6: System Field Support
                # Readonly SharePoint fields (ID, Created, Modified, Author, Editor) can be mapped
                # for pulling metadata, but must use PULL_ONLY sync direction
                is_system_field = tc.is_readonly
                sync_direction = "PULL_ONLY" if is_system_field else "BIDIRECTIONAL"

                # Map it
                db.add(FieldMapping(
                    sync_def_id=db_def.id,
                    source_column_id=sc.id,
                    target_column_id=tc.id,
                    source_column_name=sc.column_name,
                    target_column_name=tc.column_name,
                    target_type=tc.column_type, # Or derive from sc.data_type
                    is_key=sc.is_primary_key,
                    is_readonly=tc.is_readonly,
                    is_system_field=is_system_field,
                    sync_direction=sync_direction
                ))

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
    results = db.execute(stmt).scalars().all()
    
    # Enrich with names
    enriched = []
    for d in results:
        # Convert to Pydantic model first (safely handling ORM state)
        model = SyncDefinitionRead.model_validate(d)
        
        # Resolve Target List Name
        if d.target_list_id:
            sp_list = db.get(SharePointList, d.target_list_id)
            if sp_list:
                model.target_list_name = sp_list.display_name
            else:
                model.target_list_name = "Unknown List"
            
        # Resolve Source Table Name
        if d.source_table_id:
            table = db.get(DatabaseTable, d.source_table_id)
            if table:
                model.source_table_name_resolved = table.table_name
            else:
                model.source_table_name_resolved = "Unknown Table"
            
        enriched.append(model)
        
    return enriched

@router.get("/{def_id}", response_model=SyncDefinitionRead)
def get_sync_definition(
    def_id: UUID,
    db: Session = Depends(get_db)
):
    db_def = db.get(SyncDefinition, def_id)
    if not db_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")
    
    model = SyncDefinitionRead.model_validate(db_def)
    
    if db_def.target_list_id:
        sp_list = db.get(SharePointList, db_def.target_list_id)
        if sp_list:
            model.target_list_name = sp_list.display_name
            model.target_list_guid = sp_list.list_id
        else:
            model.target_list_name = "Unknown List"

    if db_def.source_table_id:
        table = db.get(DatabaseTable, db_def.source_table_id)
        if table:
            model.source_table_name_resolved = table.table_name
        else:
            model.source_table_name_resolved = "Unknown Table"

    return model

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

@router.delete("/{def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sync_definition(
    def_id: UUID,
    db: Session = Depends(get_db)
):
    db_def = db.get(SyncDefinition, def_id)
    if not db_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")
    
    db.delete(db_def)
    db.commit()
    return None
