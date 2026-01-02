from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.schemas.ops import DriftReportRequest, DriftReportResponse
from app.schemas.failover import FailoverRequest, FailoverResponse
from app.services.drift import DriftService
from app.services.failover import FailoverService
from app.services.synchronizer import Synchronizer

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

@router.post("/ingress/{sync_def_id}")
def trigger_ingress(sync_def_id: UUID, db: Session = Depends(get_db)):
    service = Synchronizer(db)
    try:
        return service.run_ingress(sync_def_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingress failed: {str(e)}")
