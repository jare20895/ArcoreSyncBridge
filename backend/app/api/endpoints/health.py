"""Health and monitoring endpoints for system diagnostics."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.api.endpoints.database_instances import get_db
from app.api.responses import success_response
from app.core.security import ADMIN_ROLES, OPERATOR_ROLES, Principal, require_roles
from app.schemas.api import ApiResponse
from app.services.audit import record_audit_event
from app.services.maintenance import MaintenanceService

router = APIRouter()
logger = logging.getLogger(__name__)

class DropSlotRequest(BaseModel):
    slot_name: str
    force: bool = False
    instance_id: Optional[str] = None

class VacuumTableRequest(BaseModel):
    schema: str
    table: str
    full: bool = False

@router.get("/cdc-health", response_model=ApiResponse[Dict[str, Any]])
def get_cdc_health(
    request: Request,
    _: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """
    Get CDC replication slot health metrics including:
    - Slot status (active/inactive)
    - Lag metrics
    - WAL directory size
    - Slot configuration vs reality
    """
    return success_response(request, MaintenanceService(db).get_cdc_health())

@router.get("/database-stats", response_model=ApiResponse[Dict[str, Any]])
def get_database_stats(
    request: Request,
    _: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Get database performance statistics"""
    return success_response(request, MaintenanceService(db).get_database_stats())

@router.post("/drop-slot", response_model=ApiResponse[Dict[str, Any]])
def drop_replication_slot(
    payload: DropSlotRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Drop a replication slot"""
    MaintenanceService(db).drop_replication_slot(payload.slot_name, payload.force, payload.instance_id)
    record_audit_event(
        db,
        request,
        principal,
        action="health.replication_slot.drop",
        resource_type="database_instance" if payload.instance_id else "system",
        resource_id=payload.instance_id or payload.slot_name,
        details={"slot_name": payload.slot_name, "force": payload.force},
    )
    return success_response(request, {
        "success": True,
        "message": f"Successfully dropped replication slot: {payload.slot_name}"
    })

@router.post("/vacuum-table", response_model=ApiResponse[Dict[str, Any]])
def vacuum_table(
    payload: VacuumTableRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    """Run VACUUM on a table"""
    MaintenanceService(db).vacuum_table(payload.schema, payload.table, payload.full)
    record_audit_event(
        db,
        request,
        principal,
        action="health.vacuum_table",
        resource_type="database_table",
        resource_id=f"{payload.schema}.{payload.table}",
        details={"full": payload.full},
    )
    return success_response(request, {
        "success": True,
        "message": f"Successfully ran {'VACUUM FULL' if payload.full else 'VACUUM'} on {payload.schema}.{payload.table}"
    })
