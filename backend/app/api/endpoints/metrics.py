"""
System and application metrics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, Any
from datetime import datetime
import psutil
import time

from app.api.endpoints.database_instances import get_db
from app.models.core import DatabaseInstance, SyncDefinition
from app.models.inventory import Application, Database, DatabaseTable, SharePointList, SyncMetric
from app.services.reconciliation import ReconciliationService

router = APIRouter()

@router.get("/counts")
def get_system_counts(db: Session = Depends(get_db)):
    """Get counts of various system entities"""
    try:
        # Count applications
        applications_count = db.query(func.count(Application.id)).scalar() or 0

        # Count databases
        databases_count = db.query(func.count(Database.id)).scalar() or 0

        # Count database instances
        instances_count = db.query(func.count(DatabaseInstance.id)).scalar() or 0

        # Count source tables
        source_tables_count = db.query(func.count(DatabaseTable.id)).scalar() or 0

        # Count SharePoint lists by status
        # Inventory: ACTIVE lists
        inventory_lists_count = db.query(func.count(SharePointList.id)).filter(
            SharePointList.status == "ACTIVE"
        ).scalar() or 0

        # Provisioned: ACTIVE and is_provisioned
        provisioned_lists_count = db.query(func.count(SharePointList.id)).filter(
            SharePointList.status == "ACTIVE",
            SharePointList.is_provisioned == True
        ).scalar() or 0

        # Deleted: status = DELETED
        deleted_lists_count = db.query(func.count(SharePointList.id)).filter(
            SharePointList.status == "DELETED"
        ).scalar() or 0

        # Count sync definitions
        sync_definitions_count = db.query(func.count(SyncDefinition.id)).scalar() or 0

        # Count active syncs (CDC enabled or scheduled)
        active_syncs_count = db.query(func.count(SyncDefinition.id)).filter(
            (SyncDefinition.cdc_enabled == True) | (SyncDefinition.schedule_enabled == True)
        ).scalar() or 0

        return {
            "applications": applications_count,
            "databases": databases_count,
            "instances": instances_count,
            "source_tables": source_tables_count,
            "sharepoint_lists": {
                "inventory": inventory_lists_count,
                "provisioned": provisioned_lists_count,
                "deleted": deleted_lists_count
            },
            "sync_definitions": sync_definitions_count,
            "active_syncs": active_syncs_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system counts: {str(e)}")

@router.post("/system-snapshot")
def get_system_snapshot(duration_seconds: int = 15):
    """
    Collect system metrics over a specified duration.
    Returns average CPU and memory usage.
    """
    if duration_seconds < 3 or duration_seconds > 60:
        raise HTTPException(status_code=400, detail="Duration must be between 3 and 60 seconds")

    try:
        # Collect system samples only
        return _collect_system_metrics_only(duration_seconds)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect system snapshot: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect system snapshot: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect system snapshot: {str(e)}")

def _get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "memory_available_gb": round(memory.available / (1024**3), 2)
    }

def _collect_system_metrics_only(duration_seconds: int) -> Dict[str, Any]:
    """Fallback when Docker is not available"""
    samples = []
    interval = 1
    num_samples = duration_seconds

    for i in range(num_samples):
        sample = _get_system_metrics()
        samples.append(sample)

        if i < num_samples - 1:
            time.sleep(interval)

    avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
    avg_memory = sum(s["memory_percent"] for s in samples) / len(samples)

    return {
        "duration_seconds": duration_seconds,
        "samples_collected": len(samples),
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": round(avg_cpu, 2),
            "memory_percent": round(avg_memory, 2),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "cpu_count": psutil.cpu_count()
        },
        "syncbridge_containers": [],
        "all_containers_count": 0
    }


@router.get("/drift-summary")
def get_drift_summary(db: Session = Depends(get_db)):
    """
    Get aggregated drift metrics across all syncs.
    Returns summary of matched/mismatched counts and total drift.
    """
    try:
        reconciliation_service = ReconciliationService(db)
        summary = reconciliation_service.get_drift_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift summary: {str(e)}")


@router.get("/drift-metrics")
def get_drift_metrics(db: Session = Depends(get_db)):
    """
    Get detailed drift metrics for all sync definitions.
    Returns list of metrics with source/target counts and drift deltas.
    """
    try:
        metrics = db.query(SyncMetric).all()

        # Join with sync definitions to get names
        result = []
        for metric in metrics:
            sync_def = db.query(SyncDefinition).filter(
                SyncDefinition.id == metric.sync_def_id
            ).first()

            result.append({
                "id": str(metric.id),
                "sync_def_id": str(metric.sync_def_id),
                "sync_def_name": sync_def.name if sync_def else "Unknown",
                "source_row_count": metric.source_row_count,
                "target_row_count": metric.target_row_count,
                "reconcile_delta": metric.reconcile_delta,
                "reconcile_status": metric.reconcile_status,
                "last_reconcile_at": metric.last_reconcile_at.isoformat() if metric.last_reconcile_at else None,
                "last_sync_ts": metric.last_sync_ts.isoformat() if metric.last_sync_ts else None,
                "total_rows_synced": metric.total_rows_synced
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift metrics: {str(e)}")


@router.post("/reconcile-drift")
def trigger_drift_reconciliation(db: Session = Depends(get_db)):
    """
    Manually trigger drift reconciliation for all syncs.
    This runs synchronously and may take some time.
    """
    try:
        reconciliation_service = ReconciliationService(db)
        summary = reconciliation_service.reconcile_all_syncs()
        return {
            "success": True,
            "message": "Drift reconciliation completed",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reconcile drift: {str(e)}")
