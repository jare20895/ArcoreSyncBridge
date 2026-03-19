"""
Drift Reconciliation Service
Calculates and tracks drift between source databases and SharePoint targets.
"""
import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models.core import SyncDefinition, SyncTarget, SyncSource, SharePointConnection, DatabaseInstance
from app.models.inventory import SyncMetric, DatabaseTable, Database
from app.services.database import DatabaseClient
from app.services.graph import GraphClient
from app.services.sharepoint_content import SharePointContentService

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Service for reconciling source and target data to detect drift."""

    def __init__(self, db: Session):
        self.db = db

    def reconcile_all_syncs(self) -> dict:
        """
        Reconcile all active sync definitions and update metrics.
        Returns summary of reconciliation results.
        """
        sync_defs = self.db.execute(
            select(SyncDefinition).where(SyncDefinition.is_paused == False)
        ).scalars().all()

        summary = {
            "total_syncs": len(sync_defs),
            "reconciled": 0,
            "failed": 0,
            "errors": []
        }

        for sync_def in sync_defs:
            try:
                self.reconcile_sync(sync_def.id)
                summary["reconciled"] += 1
            except Exception as e:
                logger.error(f"Failed to reconcile sync {sync_def.id}: {e}")
                summary["failed"] += 1
                summary["errors"].append({
                    "sync_def_id": str(sync_def.id),
                    "sync_name": sync_def.name,
                    "error": str(e)
                })

        return summary

    def reconcile_sync(self, sync_def_id: UUID) -> SyncMetric:
        """
        Reconcile a specific sync definition.
        Counts rows in source and target, calculates delta, updates metrics.
        """
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError(f"Sync definition {sync_def_id} not found")

        # Get primary source instance (supports both old and new architecture)
        primary_source = self.db.execute(
            select(SyncSource)
            .where(SyncSource.sync_def_id == sync_def_id)
            .where(SyncSource.role == "PRIMARY")
            .where(SyncSource.is_enabled == True)
        ).scalars().first()

        # Fallback: If no sync_sources entry, derive from source_table_id (old architecture)
        source_instance_id = None
        if primary_source:
            source_instance_id = primary_source.database_instance_id
        else:
            # Try to resolve from source_table_id → database_tables → databases → database_instances
            source_instance_id = self._resolve_instance_from_table(sync_def.source_table_id)
            if not source_instance_id:
                raise ValueError(f"No source instance found for sync {sync_def_id}. "
                               f"Add sync_sources entry or ensure source_table_id is valid.")

        # Get default target (supports both old and new architecture)
        default_target = self.db.execute(
            select(SyncTarget)
            .where(SyncTarget.sync_def_id == sync_def_id)
            .where(SyncTarget.is_default == True)
        ).scalars().first()

        # Fallback: If no sync_targets entry, use target_list_id from sync_definitions (old architecture)
        target_list_id = None
        target_connection_id = None
        target_site_id = None

        if default_target:
            target_list_id = default_target.target_list_id
            target_connection_id = default_target.sharepoint_connection_id
            target_site_id = default_target.site_id
        elif sync_def.target_list_id:
            # Resolve from target_list_id → sharepoint_lists
            target_list_id = sync_def.target_list_id
            target_info = self._resolve_target_from_list(sync_def.target_list_id)
            if target_info:
                target_connection_id = target_info["connection_id"]
                target_site_id = target_info["site_id"]
            else:
                logger.warning(f"Could not resolve target list {sync_def.target_list_id}")
        else:
            raise ValueError(f"No default target found for sync {sync_def_id}. "
                           f"Add sync_targets entry or ensure target_list_id is valid.")

        # Resolve source table name and schema if not in sync_def
        source_schema = sync_def.source_schema
        source_table_name = sync_def.source_table_name

        if not source_table_name and sync_def.source_table_id:
            # Resolve from database_tables
            source_table_info = self._resolve_table_info(sync_def.source_table_id)
            if source_table_info:
                source_schema = source_table_info["schema_name"] or "public"
                source_table_name = source_table_info["table_name"]

        # Count source rows
        source_count = self._count_source_rows(
            source_instance_id,
            source_schema or "public",
            source_table_name
        )

        # Resolve SharePoint list_id from internal UUID
        sp_list_id = self._resolve_sharepoint_list_id(target_list_id)

        # Count target rows
        target_count = self._count_target_rows(
            target_connection_id,
            target_site_id,
            sp_list_id
        )

        # Calculate delta
        delta = abs(source_count - target_count) if source_count is not None and target_count is not None else None

        # Determine status
        if source_count is None or target_count is None:
            status = "UNKNOWN"
        elif source_count == target_count:
            status = "MATCH"
        else:
            status = "MISMATCH"

        # Update or create sync metric
        metric = self.db.execute(
            select(SyncMetric)
            .where(SyncMetric.sync_def_id == sync_def_id)
            .where(SyncMetric.source_instance_id == source_instance_id)
            .where(SyncMetric.target_list_id == target_list_id)
        ).scalars().first()

        if not metric:
            metric = SyncMetric(
                sync_def_id=sync_def_id,
                source_instance_id=source_instance_id,
                target_list_id=target_list_id
            )
            self.db.add(metric)

        # Update metric values
        metric.source_row_count = source_count
        metric.target_row_count = target_count
        metric.reconcile_delta = delta
        metric.reconcile_status = status
        metric.last_reconcile_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(metric)

        logger.info(
            f"Reconciled sync {sync_def.name}: "
            f"source={source_count}, target={target_count}, delta={delta}, status={status}"
        )

        return metric

    def _count_source_rows(
        self,
        instance_id: UUID,
        schema: str,
        table_name: Optional[str]
    ) -> Optional[int]:
        """Count rows in source database table."""
        import psycopg

        if not table_name:
            logger.warning(f"No table name specified for instance {instance_id}")
            return None

        try:
            instance = self.db.get(DatabaseInstance, instance_id)
            if not instance:
                logger.error(f"Database instance {instance_id} not found")
                return None

            client = DatabaseClient(instance)

            # Use psycopg to connect and count
            with psycopg.connect(client.dsn) as conn:
                with conn.cursor() as cur:
                    # Sanitize identifiers
                    if not schema.replace('_', '').replace('-', '').isalnum():
                        raise ValueError(f"Invalid schema name: {schema}")
                    if not table_name.replace('_', '').replace('-', '').isalnum():
                        raise ValueError(f"Invalid table name: {table_name}")

                    query = f'SELECT COUNT(*) FROM "{schema}"."{table_name}"'
                    cur.execute(query)
                    count = cur.fetchone()[0]

                    return count

        except Exception as e:
            logger.error(f"Failed to count source rows for {schema}.{table_name}: {e}")
            return None

    def _count_target_rows(
        self,
        connection_id: Optional[UUID],
        site_id: Optional[str],
        list_id: str
    ) -> Optional[int]:
        """Count items in SharePoint list."""
        try:
            # Resolve connection
            if connection_id:
                conn = self.db.get(SharePointConnection, connection_id)
            else:
                conn = self.db.execute(
                    select(SharePointConnection).where(SharePointConnection.status == "ACTIVE")
                ).scalars().first()

            if not conn:
                logger.error("No active SharePoint connection found")
                return None

            # Get credentials
            real_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
            if not site_id:
                site_id = os.environ.get("SHAREPOINT_SITE_ID", "")

            if not site_id:
                logger.error("No site_id available")
                return None

            # Initialize Graph client
            graph = GraphClient(
                tenant_id=conn.tenant_id,
                client_id=conn.client_id,
                client_secret=real_secret,
                authority_host=conn.authority_host
            )

            content_service = SharePointContentService(graph)

            # SharePoint Graph API doesn't support $count for list items
            # We need to get all items and count them (or use pagination to estimate)
            # For now, get all items in one request (works for small to medium lists)
            items_response = graph.request(
                "GET",
                f"/sites/{site_id}/lists/{list_id}/items?$top=5000&$select=id"
            )

            if items_response and "value" in items_response:
                return len(items_response["value"])

            return 0

        except Exception as e:
            logger.error(f"Failed to count target rows for list {list_id}: {e}")
            return None

    def get_drift_summary(self) -> dict:
        """
        Get summary of drift metrics across all syncs.
        Returns aggregated drift statistics.
        """
        metrics = self.db.execute(select(SyncMetric)).scalars().all()

        total_syncs = len(metrics)
        matched = sum(1 for m in metrics if m.reconcile_status == "MATCH")
        mismatched = sum(1 for m in metrics if m.reconcile_status == "MISMATCH")
        unknown = sum(1 for m in metrics if m.reconcile_status == "UNKNOWN")

        total_drift = sum(m.reconcile_delta or 0 for m in metrics if m.reconcile_delta)

        return {
            "total_syncs": total_syncs,
            "matched": matched,
            "mismatched": mismatched,
            "unknown": unknown,
            "total_drift_items": total_drift,
            "last_updated": max(
                (m.last_reconcile_at for m in metrics if m.last_reconcile_at),
                default=None
            )
        }

    def _resolve_sharepoint_list_id(self, internal_list_id: UUID) -> Optional[str]:
        """
        Resolve SharePoint list_id from internal UUID.
        Our database uses UUID as primary key, but SharePoint uses a different list_id.
        """
        from app.models.inventory import SharePointList

        if not internal_list_id:
            return None

        try:
            sp_list = self.db.get(SharePointList, internal_list_id)
            if not sp_list:
                logger.warning(f"SharePoint list {internal_list_id} not found")
                return None

            return sp_list.list_id

        except Exception as e:
            logger.error(f"Failed to resolve SharePoint list_id from {internal_list_id}: {e}")
            return None

    def _resolve_table_info(self, source_table_id: UUID) -> Optional[dict]:
        """
        Resolve table name and schema from source_table_id.
        """
        if not source_table_id:
            return None

        try:
            table = self.db.get(DatabaseTable, source_table_id)
            if not table:
                logger.warning(f"Database table {source_table_id} not found")
                return None

            return {
                "table_name": table.table_name,
                "schema_name": table.schema_name
            }

        except Exception as e:
            logger.error(f"Failed to resolve table info from {source_table_id}: {e}")
            return None

    def _resolve_target_from_list(self, target_list_id: UUID) -> Optional[dict]:
        """
        Resolve SharePoint connection and site from target_list_id (old architecture fallback).
        target_list_id → sharepoint_lists.site_id → sharepoint_sites.connection_id
        """
        from app.models.inventory import SharePointList, SharePointSite

        if not target_list_id:
            return None

        try:
            # Get the sharepoint_list
            sp_list = self.db.get(SharePointList, target_list_id)
            if not sp_list or not sp_list.site_id:
                logger.warning(f"No site found for target_list_id {target_list_id}")
                return None

            # Get the sharepoint_site to find connection_id
            site = self.db.get(SharePointSite, sp_list.site_id)
            if not site:
                logger.warning(f"Site {sp_list.site_id} not found")
                return None

            logger.info(f"Resolved target: connection_id={site.connection_id}, site_id={site.site_id}")
            return {
                "connection_id": site.connection_id,
                "site_id": site.site_id  # This is the external SharePoint site ID
            }

        except Exception as e:
            logger.error(f"Failed to resolve target from list {target_list_id}: {e}")
            return None

    def _resolve_instance_from_table(self, source_table_id: UUID) -> Optional[UUID]:
        """
        Resolve database instance ID from source_table_id (old architecture fallback).
        source_table_id → database_tables.database_id → databases.id → database_instances.database_id
        """
        if not source_table_id:
            return None

        try:
            # Get the database_table
            table = self.db.get(DatabaseTable, source_table_id)
            if not table or not table.database_id:
                logger.warning(f"No database found for source_table_id {source_table_id}")
                return None

            # Find a database instance with matching database_id
            instance = self.db.execute(
                select(DatabaseInstance)
                .where(DatabaseInstance.database_id == table.database_id)
                .where(DatabaseInstance.status == "ACTIVE")
                .where(DatabaseInstance.role == "PRIMARY")
            ).scalars().first()

            if instance:
                logger.info(f"Resolved instance {instance.id} from source_table_id {source_table_id}")
                return instance.id
            else:
                logger.warning(f"No active primary instance found for database {table.database_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to resolve instance from table {source_table_id}: {e}")
            return None
