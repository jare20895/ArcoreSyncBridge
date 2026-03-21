from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.api.responses import success_response
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.core.security import OPERATOR_ROLES, Principal, require_roles
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.replication import (
    ReplicationSlot, CreateSlotRequest, DropSlotRequest,
    PublicationStatus, CreatePublicationRequest, DropPublicationRequest
)
from app.services.replication import ReplicationService
from app.services.publication import PublicationService
from app.services.audit import record_audit_event

router = APIRouter()

@router.get("/slots/{instance_id}", response_model=ApiResponse[List[ReplicationSlot]])
def list_replication_slots(
    instance_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        return success_response(request, service.list_slots(instance_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slots", response_model=ApiResponse[MessageResponse], status_code=status.HTTP_201_CREATED)
def create_replication_slot(
    payload: CreateSlotRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        service.create_slot(UUID(payload.instance_id), payload.slot_name, payload.plugin)
        record_audit_event(
            db,
            request,
            principal,
            action="replication.slot.create",
            resource_type="database_instance",
            resource_id=payload.instance_id,
            details={"slot_name": payload.slot_name, "plugin": payload.plugin},
        )
        return success_response(request, {"message": f"Slot {payload.slot_name} created successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/slots", response_model=ApiResponse[MessageResponse], status_code=status.HTTP_200_OK)
def drop_replication_slot(
    payload: DropSlotRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        service.drop_slot(UUID(payload.instance_id), payload.slot_name)
        record_audit_event(
            db,
            request,
            principal,
            action="replication.slot.drop",
            resource_type="database_instance",
            resource_id=payload.instance_id,
            details={"slot_name": payload.slot_name},
        )
        return success_response(request, {"message": f"Slot {payload.slot_name} dropped successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Publication Endpoints

@router.get("/publications/{instance_id}", response_model=ApiResponse[PublicationStatus])
def get_publication_status(
    instance_id: UUID,
    request: Request,
    pub_name: str = "arcore_cdc_pub",
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        return success_response(request, service.get_publication_status(instance_id, pub_name))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/publications/{instance_id}/tables", response_model=ApiResponse[List[str]])
def get_publication_available_tables(
    instance_id: UUID,
    request: Request,
    schema: str = "public",
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        return success_response(request, service.get_available_tables(instance_id, schema))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publications", response_model=ApiResponse[MessageResponse], status_code=status.HTTP_201_CREATED)
def create_publication(
    payload: CreatePublicationRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        service.create_publication(
            UUID(payload.instance_id),
            payload.pub_name,
            payload.for_all_tables,
            payload.tables
        )
        record_audit_event(
            db,
            request,
            principal,
            action="replication.publication.create",
            resource_type="database_instance",
            resource_id=payload.instance_id,
            details={"pub_name": payload.pub_name, "for_all_tables": payload.for_all_tables, "tables": payload.tables},
        )
        return success_response(request, {"message": f"Publication {payload.pub_name} created successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/publications", response_model=ApiResponse[MessageResponse], status_code=status.HTTP_200_OK)
def drop_publication(
    payload: DropPublicationRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        service.drop_publication(UUID(payload.instance_id), payload.pub_name)
        record_audit_event(
            db,
            request,
            principal,
            action="replication.publication.drop",
            resource_type="database_instance",
            resource_id=payload.instance_id,
            details={"pub_name": payload.pub_name},
        )
        return success_response(request, {"message": f"Publication {payload.pub_name} dropped successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
