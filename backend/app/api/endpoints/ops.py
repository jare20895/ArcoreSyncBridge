from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.api.endpoints.database_instances import get_db
from app.schemas.ops import DriftReportRequest, DriftReportResponse
from app.schemas.failover import FailoverRequest, FailoverResponse
from app.services.drift import DriftService
from app.services.failover import FailoverService
from app.services.synchronizer import Synchronizer
from app.services.pusher import Pusher
from app.models.core import SyncDefinition, SyncCursor, SyncRun

router = APIRouter()

@router.post("/drift-report", response_model=DriftReportResponse)
def generate_drift_report(
    request: DriftReportRequest,
    db: Session = Depends(get_db)
):
    service = DriftService(db)
    try:
        report = service.generate_report(request.sync_def_id, request.check_type)
        return report
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/failover", response_model=FailoverResponse)
def trigger_failover(
    request: FailoverRequest,
    db: Session = Depends(get_db)
):
    service = FailoverService(db)
    try:
        return service.promote_to_primary(request.new_primary_instance_id, request.old_primary_instance_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failover failed: {str(e)}")

@router.post("/sync/{sync_def_id}")
def trigger_sync(sync_def_id: UUID, db: Session = Depends(get_db)):
    """
    Triggers a sync run (Push and/or Ingress) based on the definition's mode.
    Runs synchronously for immediate feedback.
    Logs run to sync_runs table for history tracking.
    """
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    results = {}
    start_time = datetime.utcnow()

    # 1. Push (Source -> Target)
    push_run = None
    try:
        # Create run record
        push_run = SyncRun(
            sync_def_id=sync_def_id,
            run_type="PUSH",
            status="RUNNING",
            start_time=start_time
        )
        db.add(push_run)
        db.commit()
        db.refresh(push_run)

        # Execute push
        pusher = Pusher(db)
        push_res = pusher.run_push(sync_def_id)

        # Update run record
        push_run.status = "COMPLETED" if push_res.get("failed_count", 0) == 0 else "FAILED"
        push_run.end_time = datetime.utcnow()
        push_run.items_processed = push_res.get("processed_count", 0)
        push_run.items_failed = push_res.get("failed_count", 0)
        db.commit()

        results["push"] = push_res
    except Exception as e:
        if push_run:
            push_run.status = "FAILED"
            push_run.end_time = datetime.utcnow()
            push_run.error_message = str(e)
            db.commit()
        results["push"] = {"error": str(e)}

    # 2. Ingress (Target -> Source)
    if sync_def.sync_mode == "TWO_WAY":
        ingress_run = None
        try:
            # Create run record
            ingress_run = SyncRun(
                sync_def_id=sync_def_id,
                run_type="INGRESS",
                status="RUNNING",
                start_time=datetime.utcnow()
            )
            db.add(ingress_run)
            db.commit()
            db.refresh(ingress_run)

            # Execute ingress
            syncer = Synchronizer(db)
            ingress_res = syncer.run_ingress(sync_def_id)

            # Update run record
            ingress_run.status = "COMPLETED"
            ingress_run.end_time = datetime.utcnow()
            ingress_run.items_processed = ingress_res.get("processed_count", 0)
            db.commit()

            results["ingress"] = ingress_res
        except Exception as e:
            if ingress_run:
                ingress_run.status = "FAILED"
                ingress_run.end_time = datetime.utcnow()
                ingress_run.error_message = str(e)
                db.commit()
            results["ingress"] = {"error": str(e)}

    return results

@router.post("/ingress/{sync_def_id}")
def trigger_ingress(sync_def_id: UUID, db: Session = Depends(get_db)):
    service = Synchronizer(db)
    try:
        return service.run_ingress(sync_def_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingress failed: {str(e)}")

@router.delete("/sync/{sync_def_id}/cursors")
def reset_cursors(sync_def_id: UUID, db: Session = Depends(get_db)):
    """
    Deletes all sync cursors for a sync definition.
    This forces the next sync to start from the beginning (all rows).
    Useful for testing and recovering from failed syncs.
    """
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    try:
        # Delete all cursors for this sync definition
        stmt = delete(SyncCursor).where(SyncCursor.sync_def_id == sync_def_id)
        result = db.execute(stmt)
        db.commit()

        deleted_count = result.rowcount
        return {
            "message": f"Reset {deleted_count} cursor(s) for sync definition",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset cursors: {str(e)}")
