from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import OPERATOR_ROLES, require_roles
from app.db.session import SessionLocal
from app.models.core import SyncDefinition, SyncSource, DatabaseInstance


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cdc_manager(request: Request):
    """Get CDC manager from app state."""
    return request.app.state.cdc_manager


@router.post("/{sync_def_id}/enable-cdc")
def enable_cdc(
    sync_def_id: UUID,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
    cdc_manager = Depends(get_cdc_manager)
):
    """
    Enable CDC (Change Data Capture) for a sync definition.

    This will:
    1. Set cdc_enabled=True on the sync definition
    2. Start CDC thread for the database instance if not already running
    """
    # Get sync definition
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    # Get primary source to determine database instance
    stmt = select(SyncSource).where(
        SyncSource.sync_def_id == sync_def_id,
        SyncSource.role == "PRIMARY"
    )
    source = db.execute(stmt).scalar_one_or_none()

    database_instance_id = None
    if source:
        database_instance_id = source.database_instance_id
    elif sync_def.source_table_id:
        # Fallback: Infer instance from Source Table ID
        from app.models.inventory import DatabaseTable
        
        table = db.get(DatabaseTable, sync_def.source_table_id)
        if table:
            # Find an active instance for this table's database
            instance_stmt = select(DatabaseInstance).where(
                DatabaseInstance.database_id == table.database_id,
                DatabaseInstance.status == "ACTIVE"
            ).order_by(DatabaseInstance.priority) # Prioritize lower number (1 = primary)
            
            db_instance = db.execute(instance_stmt).scalars().first()
            if db_instance:
                database_instance_id = db_instance.id

    if not database_instance_id:
        raise HTTPException(
            status_code=400,
            detail="Sync definition has no primary source (and could not infer from inventory)"
        )

    # Verify instance exists
    instance = db.get(DatabaseInstance, database_instance_id)
    if not instance:
        raise HTTPException(
            status_code=404,
            detail="Database instance not found"
        )

    # Verify replication slot exists
    if not instance.replication_slot_name:
        raise HTTPException(
            status_code=400,
            detail="Database instance does not have a replication slot configured. "
                   "Please assign a replication slot first using the replication endpoints."
        )

    # Enable CDC on sync definition
    sync_def.cdc_enabled = True
    db.commit()

    # Start CDC thread for instance (if not already running)
    if cdc_manager:
        cdc_manager.start_cdc_for_instance(database_instance_id)

    return {
        "message": "CDC enabled successfully",
        "sync_def_id": str(sync_def_id),
        "instance_id": str(database_instance_id),
        "cdc_status": "active"
    }


@router.post("/{sync_def_id}/disable-cdc")
def disable_cdc(
    sync_def_id: UUID,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """
    Disable CDC for a sync definition.

    This will set cdc_enabled=False. The CDC thread will continue running
    but this specific sync definition will be ignored by the consumer.
    """
    # Get sync definition
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    # Disable CDC
    sync_def.cdc_enabled = False
    db.commit()

    return {
        "message": "CDC disabled successfully",
        "sync_def_id": str(sync_def_id),
        "cdc_status": "disabled"
    }


@router.get("/status")
def get_cdc_status(cdc_manager = Depends(get_cdc_manager)):
    """Get status of CDC Manager and running threads."""
    if not cdc_manager:
        return {
            "status": "not_initialized",
            "running_instances": 0
        }

    return {
        "status": "running",
        **cdc_manager.get_status()
    }
