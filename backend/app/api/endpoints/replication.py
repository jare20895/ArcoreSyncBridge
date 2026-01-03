from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.schemas.replication import ReplicationSlot, CreateSlotRequest, DropSlotRequest
from app.services.replication import ReplicationService

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
