from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import psycopg2
from psycopg2 import sql as psycopg2_sql
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.core import DatabaseInstance
from app.schemas.database_instance import ConnectionTestResult
from app.services.database import DatabaseClient


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def system_dsn() -> str:
        return (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    @classmethod
    def connect_system_db(cls):
        conn = psycopg2.connect(cls.system_dsn())
        conn.autocommit = True
        return conn

    @staticmethod
    def _validate_identifier_part(value: str, field_name: str) -> None:
        if not value.replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail=f"Invalid {field_name}")

    @staticmethod
    def _wait_for_slot_release(cur, slot_name: str, attempts: int = 5, sleep_seconds: float = 0.5) -> None:
        import time

        for _ in range(attempts):
            time.sleep(sleep_seconds)
            cur.execute(
                "SELECT active_pid FROM pg_replication_slots WHERE slot_name = %s",
                (slot_name,),
            )
            check_row = cur.fetchone()
            if check_row and not check_row[0]:
                return

    @staticmethod
    def _build_vacuum_statement(schema_name: str, table_name: str, full: bool):
        base = "VACUUM FULL {}.{}" if full else "VACUUM {}.{}"
        return psycopg2_sql.SQL(base).format(
            psycopg2_sql.Identifier(schema_name),
            psycopg2_sql.Identifier(table_name),
        )

    @staticmethod
    def _drop_slot_with_client(client: DatabaseClient, slot_name: str, force: bool) -> None:
        rows = client.execute_raw(
            "SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = %s",
            (slot_name,),
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Replication slot '{slot_name}' not found on instance")

        _, active_pid = rows[0]
        if active_pid and force:
            client.execute_raw(
                "SELECT pg_terminate_backend(%s)",
                (active_pid,),
                autocommit=True,
            )

        try:
            client.execute_raw(
                "SELECT pg_drop_replication_slot(%s)",
                (slot_name,),
                autocommit=True,
            )
        except Exception as exc:
            if "is active" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail=f"Replication slot '{slot_name}' is active. Use force=true to terminate the connection first.",
                ) from exc
            raise

    @classmethod
    def _drop_slot_with_cursor(cls, cur, slot_name: str, force: bool) -> None:
        cur.execute(
            "SELECT slot_name, active_pid FROM pg_replication_slots WHERE slot_name = %s",
            (slot_name,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Replication slot '{slot_name}' not found")

        _, active_pid = row
        if active_pid and force:
            cur.execute("SELECT pg_terminate_backend(%s)", (active_pid,))
            cls._wait_for_slot_release(cur, slot_name)

        try:
            cur.execute("SELECT pg_drop_replication_slot(%s)", (slot_name,))
        except Exception as exc:
            if "is active" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail=f"Replication slot '{slot_name}' is active. Use force=true to terminate the connection first.",
                ) from exc
            raise

    @staticmethod
    def _run_connection_test(
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        success_message: str,
    ) -> ConnectionTestResult:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5,
            )
            conn.close()
            return ConnectionTestResult(success=True, message=success_message)
        except psycopg2.OperationalError as exc:
            return ConnectionTestResult(success=False, message=f"Connection failed: {exc}")
        except Exception as exc:
            return ConnectionTestResult(success=False, message=f"Unexpected error: {exc}")

    def test_connection_request(
        self,
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ) -> ConnectionTestResult:
        return self._run_connection_test(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            success_message="Connection successful!",
        )

    def test_stored_instance_connection(self, instance_id: UUID) -> ConnectionTestResult:
        db_instance = self.db.get(DatabaseInstance, instance_id)
        if not db_instance:
            raise HTTPException(status_code=404, detail="Database instance not found")

        if not db_instance.db_name or not db_instance.username or not db_instance.password:
            return ConnectionTestResult(
                success=False,
                message="Missing database name, username, or password in stored instance",
            )

        return self._run_connection_test(
            host=db_instance.host,
            port=db_instance.port,
            database=db_instance.db_name,
            user=db_instance.username,
            password=db_instance.password,
            success_message="Connection successful (using stored credentials)",
        )

    def get_cdc_health(self) -> Dict[str, Any]:
        try:
            conn = self.connect_system_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        pg_current_wal_lsn() as current_lsn,
                        pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') as wal_position_bytes
                    """
                )
                wal_info = cur.fetchone()

                cur.execute("SELECT pg_size_pretty(SUM(size)) as wal_size, SUM(size) as wal_size_bytes FROM pg_ls_waldir()")
                wal_dir = cur.fetchone()

                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_connections,
                        COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                        COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                        COUNT(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    """
                )
                conn_stats = cur.fetchone()
            conn.close()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to get CDC health: {exc}") from exc

        slot_data = []
        try:
            conn = self.connect_system_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
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
                )
                local_slots = cur.fetchall()
                for slot in local_slots:
                    slot_name, slot_type, database, active, restart_lsn, flush_lsn, lag_bytes, flush_lag_bytes = slot
                    slot_data.append(
                        {
                            "slot_name": slot_name,
                            "slot_type": slot_type,
                            "database": database,
                            "instance_label": "System (Local)",
                            "instance_id": None,
                            "active": active,
                            "restart_lsn": str(restart_lsn) if restart_lsn else None,
                            "confirmed_flush_lsn": str(flush_lsn) if flush_lsn else None,
                            "lag_bytes": lag_bytes,
                            "lag_mb": round(lag_bytes / (1024 * 1024), 2) if lag_bytes else None,
                            "flush_lag_bytes": flush_lag_bytes,
                            "flush_lag_mb": round(flush_lag_bytes / (1024 * 1024), 2) if flush_lag_bytes else None,
                        }
                    )
            conn.close()
        except Exception:
            pass

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

        instances = self.db.execute(select(DatabaseInstance)).scalars().all()
        for instance in instances:
            try:
                client = DatabaseClient(instance)
                remote_slots = client.execute_raw(slot_query)
                for slot in remote_slots:
                    slot_name, slot_type, database, active, restart_lsn, flush_lsn, lag_bytes, flush_lag_bytes = slot
                    slot_data.append(
                        {
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
                        }
                    )
            except Exception:
                continue

        inactive_slots = sum(1 for slot in slot_data if not slot["active"])
        high_lag_slots = sum(1 for slot in slot_data if slot["lag_mb"] and slot["lag_mb"] > 100)
        wal_size_bytes = wal_dir[1] if wal_dir and wal_dir[1] else 0

        status = "healthy"
        issues = []
        if inactive_slots > 0:
            status = "warning"
            issues.append(f"{inactive_slots} inactive slot(s) preventing WAL cleanup")
        if high_lag_slots > 0:
            status = "warning" if status == "healthy" else "critical"
            issues.append(f"{high_lag_slots} slot(s) with high lag (>100MB)")
        if wal_size_bytes > 1024 * 1024 * 1024:
            status = "warning" if status == "healthy" else status
            issues.append(f"System WAL directory size is {wal_dir[0] if wal_dir else 'Unknown'}")
        if conn_stats and conn_stats[1] > 50:
            status = "warning" if status == "healthy" else status
            issues.append(f"{conn_stats[1]} active connections on System DB")

        return {
            "status": status,
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
            "wal": {
                "current_lsn": str(wal_info[0]) if wal_info else None,
                "position_bytes": wal_info[1] if wal_info else 0,
                "position_mb": round(wal_info[1] / (1024 * 1024), 2) if wal_info and wal_info[1] else 0,
                "directory_size": wal_dir[0] if wal_dir else "0B",
                "directory_size_bytes": wal_dir[1] if wal_dir else 0,
            },
            "slots": slot_data,
            "connections": {
                "total": conn_stats[0] if conn_stats else 0,
                "active": conn_stats[1] if conn_stats else 0,
                "idle": conn_stats[2] if conn_stats else 0,
                "waiting": conn_stats[3] if conn_stats else 0,
            },
        }

    def get_database_stats(self) -> Dict[str, Any]:
        try:
            conn = self.connect_system_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
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
                    """
                )
                tables = cur.fetchall()

                table_data = []
                for table in tables:
                    schema, name, size, size_bytes, mods, tuples_count = table
                    table_data.append(
                        {
                            "schema": schema,
                            "table": name,
                            "size": size,
                            "size_bytes": size_bytes,
                            "modifications": mods,
                            "live_tuples": tuples_count,
                        }
                    )

                cur.execute(
                    """
                    SELECT
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit) as heap_hit,
                        CASE WHEN sum(heap_blks_hit) + sum(heap_blks_read) > 0
                            THEN round(100.0 * sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)), 2)
                            ELSE 100
                        END as cache_hit_ratio
                    FROM pg_statio_user_tables
                    """
                )
                cache_stats = cur.fetchone()
            conn.close()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to get database stats: {exc}") from exc

        return {
            "tables": table_data,
            "cache_hit_ratio": float(cache_stats[2]) if cache_stats[2] else 100.0,
            "heap_blocks_read": cache_stats[0],
            "heap_blocks_hit": cache_stats[1],
        }

    def drop_replication_slot(self, slot_name: str, force: bool, instance_id: Optional[str] = None) -> None:
        if instance_id:
            instance = self.db.get(DatabaseInstance, UUID(instance_id))
            if not instance:
                raise HTTPException(status_code=404, detail="Database instance not found")
            self._drop_slot_with_client(DatabaseClient(instance), slot_name, force)
            return

        conn = self.connect_system_db()
        try:
            with conn.cursor() as cur:
                self._drop_slot_with_cursor(cur, slot_name, force)
        finally:
            conn.close()

    def vacuum_table(self, schema_name: str, table_name: str, full: bool) -> None:
        self._validate_identifier_part(schema_name, "schema name")
        self._validate_identifier_part(table_name, "table name")

        conn = self.connect_system_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename = %s",
                    (schema_name, table_name),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Table '{schema_name}.{table_name}' not found")

                cur.execute(self._build_vacuum_statement(schema_name, table_name, full))
        finally:
            conn.close()
