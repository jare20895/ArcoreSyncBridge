from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.schemas.replication import (
    ReplicationSlot, CreateSlotRequest, DropSlotRequest,
    PublicationStatus, CreatePublicationRequest, DropPublicationRequest
)
from app.services.replication import ReplicationService
from app.services.publication import PublicationService

router = APIRouter()

@router.get("/slots/{instance_id}", response_model=List[ReplicationSlot])
def list_replication_slots(
    instance_id: UUID,
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        return service.list_slots(instance_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slots", status_code=status.HTTP_201_CREATED)
def create_replication_slot(
    request: CreateSlotRequest,
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        service.create_slot(UUID(request.instance_id), request.slot_name, request.plugin)
        return {"message": f"Slot {request.slot_name} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/slots", status_code=status.HTTP_200_OK)
def drop_replication_slot(
    request: DropSlotRequest,
    db: Session = Depends(get_db)
):
    service = ReplicationService(db)
    try:
        service.drop_slot(UUID(request.instance_id), request.slot_name)
        return {"message": f"Slot {request.slot_name} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Publication Endpoints

@router.get("/publications/{instance_id}", response_model=PublicationStatus)
def get_publication_status(
    instance_id: UUID,
    pub_name: str = "arcore_cdc_pub",
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        return service.get_publication_status(instance_id, pub_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/publications/{instance_id}/tables", response_model=List[str])
def get_publication_available_tables(
    instance_id: UUID,
    schema: str = "public",
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        return service.get_available_tables(instance_id, schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publications", status_code=status.HTTP_201_CREATED)
def create_publication(
    request: CreatePublicationRequest,
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        service.create_publication(
            UUID(request.instance_id),
            request.pub_name,
            request.for_all_tables,
            request.tables
        )
        return {"message": f"Publication {request.pub_name} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/publications", status_code=status.HTTP_200_OK)
def drop_publication(
    request: DropPublicationRequest,
    db: Session = Depends(get_db)
):
    service = PublicationService(db)
    try:
        service.drop_publication(UUID(request.instance_id), request.pub_name)
        return {"message": f"Publication {request.pub_name} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
