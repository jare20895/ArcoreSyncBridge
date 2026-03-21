"""
Health and monitoring endpoints for system diagnostics
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, select
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.api.endpoints.database_instances import get_db
from app.api.responses import success_response
from app.core.config import settings
from app.core.security import ADMIN_ROLES, OPERATOR_ROLES, Principal, require_roles
from app.models.core import DatabaseInstance
from app.schemas.api import ApiResponse
from app.services.database import DatabaseClient
from app.services.audit import record_audit_event
import psycopg2

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
def get_cdc_health(request: Request, db: Session = Depends(get_db)):
    """
    Get CDC replication slot health metrics including:
    - Slot status (active/inactive)
    - Lag metrics
    - WAL directory size
    - Slot configuration vs reality
    """
    try:
        # Connect to the main database for system WAL checks
        dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        conn = psycopg2.connect(dsn)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Get WAL status (System)
            cur.execute("""
                SELECT
                    pg_current_wal_lsn() as current_lsn,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') as wal_position_bytes
            """)
            wal_info = cur.fetchone()

            # Get WAL directory size (System)
            cur.execute("SELECT pg_size_pretty(SUM(size)) as wal_size, SUM(size) as wal_size_bytes FROM pg_ls_waldir()")
            wal_dir = cur.fetchone()

            # Get database activity stats (System)
            cur.execute("""
                SELECT
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                    COUNT(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            conn_stats = cur.fetchone()
        
        conn.close()

        # Collect slots from ALL sources
        slot_data = []
        
        # 1. Local System Slots (Legacy/System)
        try:
            conn = psycopg2.connect(dsn)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        slot_name,
                        slot_type,
                        database,
                        active,
                        restart_lsn,
                        confirmed_flush_lsn,
                        pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes,
                        pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) as flush_lag_bytes
                    FROM pg_replication_slots
                    ORDER BY lag_bytes DESC NULLS LAST
                """)
                local_slots = cur.fetchall()
                for slot in local_slots:
                    slot_name, slot_type, database, active, restart_lsn, flush_lsn, lag_bytes, flush_lag_bytes = slot
                    slot_data.append({
                        "slot_name": slot_name,
                        "slot_type": slot_type,
                        "database": database, # DB Name
                        "instance_label": "System (Local)",
                        "instance_id": None,
                        "active": active,
                        "restart_lsn": str(restart_lsn) if restart_lsn else None,
                        "confirmed_flush_lsn": str(flush_lsn) if flush_lsn else None,
                        "lag_bytes": lag_bytes,
                        "lag_mb": round(lag_bytes / (1024 * 1024), 2) if lag_bytes else None,
                        "flush_lag_bytes": flush_lag_bytes,
                        "flush_lag_mb": round(flush_lag_bytes / (1024 * 1024), 2) if flush_lag_bytes else None,
                    })
            conn.close()
        except Exception:
            logger.exception("health_local_slot_fetch_failed")

        # 2. Registered Instance Slots
        instances = db.execute(select(DatabaseInstance)).scalars().all()
        
        slot_query = """
            SELECT
                slot_name,
                slot_type,
                database,
                active,
                restart_lsn,
                confirmed_flush_lsn,
                pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes,
                pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) as flush_lag_bytes
            FROM pg_replication_slots
            ORDER BY lag_bytes DESC NULLS LAST
        """

        for instance in instances:
            try:
                client = DatabaseClient(instance)
                # DatabaseClient.execute_raw returns list of tuples
                remote_slots = client.execute_raw(slot_query)
                
                for slot in remote_slots:
                    slot_name, slot_type, database, active, restart_lsn, flush_lsn, lag_bytes, flush_lag_bytes = slot
                    slot_data.append({
                        "slot_name": slot_name,
                        "slot_type": slot_type,
                        "database": database,
                        "instance_label": instance.instance_label,
                        "instance_id": str(instance.id),
                        "active": active,
                        "restart_lsn": str(restart_lsn) if restart_lsn else None,
                        "confirmed_flush_lsn": str(flush_lsn) if flush_lsn else None,
                        "lag_bytes": lag_bytes,
                        "lag_mb": round(lag_bytes / (1024 * 1024), 2) if lag_bytes is not None else None,
                        "flush_lag_bytes": flush_lag_bytes,
                        "flush_lag_mb": round(flush_lag_bytes / (1024 * 1024), 2) if flush_lag_bytes is not None else None,
                    })
            except Exception:
                # Log but continue
                logger.exception("health_remote_slot_fetch_failed instance_label=%s", instance.instance_label)
                # Optionally add an error marker to UI?

        # Determine health status (Aggregate)
        inactive_slots = sum(1 for s in slot_data if not s["active"])
        high_lag_slots = sum(1 for s in slot_data if s["lag_mb"] and s["lag_mb"] > 100)
        wal_size_bytes = wal_dir[1] if wal_dir and wal_dir[1] else 0

        status = "healthy"
        issues = []

        if inactive_slots > 0:
            status = "warning"
            issues.append(f"{inactive_slots} inactive slot(s) preventing WAL cleanup")

        if high_lag_slots > 0:
            status = "warning" if status == "healthy" else "critical"
            issues.append(f"{high_lag_slots} slot(s) with high lag (>100MB)")

        if wal_size_bytes > 1024 * 1024 * 1024:  # > 1GB
            status = "warning" if status == "healthy" else status
            issues.append(f"System WAL directory size is {wal_dir[0] if wal_dir else 'Unknown'}")

        if conn_stats and conn_stats[1] > 50:  # > 50 active connections
            status = "warning" if status == "healthy" else status
            issues.append(f"{conn_stats[1]} active connections on System DB")

        return success_response(request, {
            "status": status,
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
            "wal": {
                "current_lsn": str(wal_info[0]) if wal_info else None,
                "position_bytes": wal_info[1] if wal_info else 0,
                "position_mb": round(wal_info[1] / (1024 * 1024), 2) if wal_info and wal_info[1] else 0,
                "directory_size": wal_dir[0] if wal_dir else "0B",
                "directory_size_bytes": wal_dir[1] if wal_dir else 0
            },
            "slots": slot_data,
            "connections": {
                "total": conn_stats[0] if conn_stats else 0,
                "active": conn_stats[1] if conn_stats else 0,
                "idle": conn_stats[2] if conn_stats else 0,
                "waiting": conn_stats[3] if conn_stats else 0
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CDC health: {str(e)}")

@router.get("/database-stats", response_model=ApiResponse[Dict[str, Any]])
def get_database_stats(request: Request, db: Session = Depends(get_db)):
    """Get database performance statistics"""
    try:
        dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        conn = psycopg2.connect(dsn)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Get table sizes
            cur.execute("""
                SELECT
                    schemaname,
                    relname,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                    pg_total_relation_size(schemaname||'.'||relname) as total_size_bytes,
                    n_tup_ins + n_tup_upd + n_tup_del as total_modifications,
                    n_live_tup as live_tuples
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC
                LIMIT 10
            """)
            tables = cur.fetchall()

            table_data = []
            for table in tables:
                schema, name, size, size_bytes, mods, tuples = table
                table_data.append({
                    "schema": schema,
                    "table": name,
                    "size": size,
                    "size_bytes": size_bytes,
                    "modifications": mods,
                    "live_tuples": tuples
                })

            # Get cache hit ratio
            cur.execute("""
                SELECT
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    CASE WHEN sum(heap_blks_hit) + sum(heap_blks_read) > 0
                        THEN round(100.0 * sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)), 2)
                        ELSE 100
                    END as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            cache_stats = cur.fetchone()

            conn.close()

            return success_response(request, {
                "tables": table_data,
                "cache_hit_ratio": float(cache_stats[2]) if cache_stats[2] else 100.0,
                "heap_blocks_read": cache_stats[0],
                "heap_blocks_hit": cache_stats[1]
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")

@router.post("/drop-slot", response_model=ApiResponse[Dict[str, Any]])
def drop_replication_slot(
    payload: DropSlotRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Drop a replication slot"""
    try:
        if payload.instance_id:
            # Drop from specific instance using DatabaseClient/Replication logic
            instance = db.get(DatabaseInstance, UUID(payload.instance_id))
            if not instance:
                raise HTTPException(status_code=404, detail="Database instance not found")
            
            client = DatabaseClient(instance)
            
            # Check existence
            try:
                rows = client.execute_raw("SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = %s", (payload.slot_name,))
                if not rows:
                    raise HTTPException(status_code=404, detail=f"Replication slot '{payload.slot_name}' not found on instance")
                
                slot_name, active_pid = rows[0]
                
                if active_pid and payload.force:
                    client.execute_raw(f"SELECT pg_terminate_backend({active_pid})", autocommit=True)
                    # Wait/Retry logic could be added here similar to below, but keeping it simple for now or copying it
                
                client.execute_raw(f"SELECT pg_drop_replication_slot('{request.slot_name}')", autocommit=True)
                
            except Exception as e:
                error_str = str(e)
                if "is active" in error_str:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Replication slot '{payload.slot_name}' is active. Use force=true to terminate the connection first."
                    )
                raise HTTPException(status_code=500, detail=f"Failed to drop slot: {str(e)}")

        else:
            # Legacy/System drop (Local DB)
            dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            conn = psycopg2.connect(dsn)
            conn.autocommit = True

            with conn.cursor() as cur:
                # Check if slot exists and get active pid
                cur.execute(
                    "SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = %s",
                    (payload.slot_name,)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail=f"Replication slot '{payload.slot_name}' not found")

                slot_name, active_pid = row

                # If slot is active and force=True, terminate the backend
                if active_pid and payload.force:
                    cur.execute(f"SELECT pg_terminate_backend({active_pid})")
                    # Wait for the backend to terminate and retry a few times
                    import time
                    for i in range(5):
                        time.sleep(0.5)
                        cur.execute(
                            "SELECT active_pid FROM pg_replication_slots WHERE slot_name = %s",
                            (payload.slot_name,)
                        )
                        check_row = cur.fetchone()
                        if check_row and not check_row[0]:
                            # Slot is no longer active
                            break

                # Drop the slot
                try:
                    cur.execute(f"SELECT pg_drop_replication_slot('{request.slot_name}')")
                except Exception as e:
                    error_str = str(e)
                    if "is active" in error_str:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Replication slot '{payload.slot_name}' is active. Use force=true to terminate the connection first."
                        )
                    raise

            conn.close()

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to drop replication slot: {str(e)}")

@router.post("/vacuum-table", response_model=ApiResponse[Dict[str, Any]])
def vacuum_table(
    payload: VacuumTableRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    """Run VACUUM on a table"""
    try:
        # Validate schema and table name to prevent SQL injection
        if not payload.schema.replace('_', '').isalnum():
            raise HTTPException(status_code=400, detail="Invalid schema name")
        if not payload.table.replace('_', '').isalnum():
            raise HTTPException(status_code=400, detail="Invalid table name")

        dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        conn = psycopg2.connect(dsn)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Check if table exists
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename = %s",
                (payload.schema, payload.table)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail=f"Table '{payload.schema}.{payload.table}' not found")

            # Run VACUUM
            vacuum_cmd = f"VACUUM {'FULL' if payload.full else ''} {payload.schema}.{payload.table}"
            cur.execute(vacuum_cmd)

        conn.close()

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to vacuum table: {str(e)}")
