from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.responses import success_response
from app.api.endpoints.database_instances import get_db
from app.core.security import EDITOR_ROLES, VIEWER_ROLES, Principal, require_roles
from app.models.core import FieldMapping, SyncDefinition
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.sync_definition import FieldMappingCreate, FieldMappingRead
from app.services.audit import record_audit_event

router = APIRouter()

@router.post("/", response_model=ApiResponse[FieldMappingRead], status_code=status.HTTP_201_CREATED)
def create_field_mapping(
    mapping_in: FieldMappingCreate,
    sync_def_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    """Create a new field mapping for a sync definition."""
    # Verify sync definition exists
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    # Create field mapping
    db_mapping = FieldMapping(
        sync_def_id=sync_def_id,
        **mapping_in.model_dump()
    )
    db.add(db_mapping)

    try:
        db.commit()
        db.refresh(db_mapping)
        record_audit_event(
            db,
            request,
            principal,
            action="field_mapping.create",
            resource_type="field_mapping",
            resource_id=str(db_mapping.id),
            details={"sync_def_id": str(sync_def_id)},
        )
        return success_response(request, db_mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sync-definition/{sync_def_id}", response_model=ApiResponse[List[FieldMappingRead]])
def list_field_mappings_by_sync_def(
    sync_def_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db)
):
    """Get all field mappings for a specific sync definition."""
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    stmt = select(FieldMapping).where(FieldMapping.sync_def_id == sync_def_id)
    mappings = db.execute(stmt).scalars().all()
    return success_response(request, mappings)

@router.get("/{mapping_id}", response_model=ApiResponse[FieldMappingRead])
def get_field_mapping(
    mapping_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db)
):
    """Get a specific field mapping by ID."""
    db_mapping = db.get(FieldMapping, mapping_id)
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Field mapping not found")
    return success_response(request, db_mapping)

@router.put("/{mapping_id}", response_model=ApiResponse[FieldMappingRead])
def update_field_mapping(
    mapping_id: UUID,
    mapping_in: FieldMappingCreate,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    """Update an existing field mapping."""
    db_mapping = db.get(FieldMapping, mapping_id)
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Field mapping not found")

    # Update fields
    update_data = mapping_in.model_dump()
    for field, value in update_data.items():
        setattr(db_mapping, field, value)

    try:
        db.commit()
        db.refresh(db_mapping)
        record_audit_event(
            db,
            request,
            principal,
            action="field_mapping.update",
            resource_type="field_mapping",
            resource_id=str(db_mapping.id),
            details={"sync_def_id": str(db_mapping.sync_def_id)},
        )
        return success_response(request, db_mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{mapping_id}", response_model=ApiResponse[MessageResponse])
def delete_field_mapping(
    mapping_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    """Delete a field mapping."""
    db_mapping = db.get(FieldMapping, mapping_id)
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Field mapping not found")

    db.delete(db_mapping)
    db.commit()
    record_audit_event(
        db,
        request,
        principal,
        action="field_mapping.delete",
        resource_type="field_mapping",
        resource_id=str(mapping_id),
        details={"sync_def_id": str(db_mapping.sync_def_id)},
    )
    return success_response(request, {"message": "Field mapping deleted"})

@router.post("/sync-definition/{sync_def_id}/bulk", response_model=ApiResponse[List[FieldMappingRead]])
def bulk_update_field_mappings(
    sync_def_id: UUID,
    mappings_in: List[FieldMappingCreate],
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Bulk update field mappings for a sync definition.
    This replaces all existing mappings with the provided list.
    """
    # Verify sync definition exists
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    # Delete all existing mappings for this sync definition
    db.execute(
        select(FieldMapping).where(FieldMapping.sync_def_id == sync_def_id)
    )
    existing_mappings = db.execute(
        select(FieldMapping).where(FieldMapping.sync_def_id == sync_def_id)
    ).scalars().all()

    for mapping in existing_mappings:
        db.delete(mapping)

    # Create new mappings
    new_mappings = []
    for mapping_data in mappings_in:
        db_mapping = FieldMapping(
            sync_def_id=sync_def_id,
            **mapping_data.model_dump()
        )
        db.add(db_mapping)
        new_mappings.append(db_mapping)

    try:
        db.commit()
        for mapping in new_mappings:
            db.refresh(mapping)
        record_audit_event(
            db,
            request,
            principal,
            action="field_mapping.bulk_replace",
            resource_type="sync_definition",
            resource_id=str(sync_def_id),
            details={"mapping_count": len(new_mappings)},
        )
        return success_response(request, new_mappings)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
