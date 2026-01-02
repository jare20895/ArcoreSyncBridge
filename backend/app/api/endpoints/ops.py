from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.schemas.ops import DriftReportRequest, DriftReportResponse
from app.schemas.failover import FailoverRequest, FailoverResponse
from app.services.drift import DriftService
from app.services.failover import FailoverService
from app.services.synchronizer import Synchronizer
from app.services.pusher import Pusher
from app.models.core import SyncDefinition

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
    """
    sync_def = db.get(SyncDefinition, sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")

    results = {}
    
    # 1. Push (Source -> Target)
    # Always run push unless we add a "PULL_ONLY" mode later.
    try:
        pusher = Pusher(db)
        push_res = pusher.run_push(sync_def_id)
        results["push"] = push_res
    except Exception as e:
        results["push"] = {"error": str(e)}
        # We continue to ingress if Two-Way? Maybe. 

    # 2. Ingress (Target -> Source)
    if sync_def.sync_mode == "TWO_WAY":
        try:
            syncer = Synchronizer(db)
            ingress_res = syncer.run_ingress(sync_def_id)
            results["ingress"] = ingress_res
        except Exception as e:
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
