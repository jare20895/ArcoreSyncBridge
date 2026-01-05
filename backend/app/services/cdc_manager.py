import logging
import threading
from typing import Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import DatabaseInstance, SyncDefinition, SyncSource
from app.services.cdc import CDCService

logger = logging.getLogger(__name__)


class CDCManager:
    """
    Manages CDC service threads per database instance.

    Maintains a registry of running CDC threads and provides methods to
    start/stop CDC for specific instances or all enabled instances.
    """

    def __init__(self, db: Session):
        self.db = db
        # Registry: instance_id -> (CDCService, Thread, StopEvent)
        self.registry: Dict[UUID, Tuple[CDCService, threading.Thread, threading.Event]] = {}
        self.lock = threading.Lock()

    def start_cdc_for_instance(self, instance_id: UUID) -> bool:
        """
        Start CDC for a specific database instance.

        Returns:
            True if CDC was started, False if already running
        """
        with self.lock:
            if instance_id in self.registry:
                logger.warning(f"CDC already running for instance {instance_id}")
                return False

            try:
                # Create stop event for graceful shutdown
                stop_event = threading.Event()

                # Create CDC service with its own DB session
                # Note: CDCService will create its own session internally
                from app.db.session import SessionLocal
                cdc_session = SessionLocal()

                cdc_service = CDCService(cdc_session, instance_id, stop_event)

                # Create and start thread
                thread = threading.Thread(
                    target=cdc_service.run,
                    name=f"CDC-{instance_id}",
                    daemon=True
                )
                thread.start()

                # Register
                self.registry[instance_id] = (cdc_service, thread, stop_event)
                logger.info(f"Started CDC for instance {instance_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to start CDC for instance {instance_id}: {e}")
                return False

    def stop_cdc_for_instance(self, instance_id: UUID) -> bool:
        """
        Stop CDC for a specific database instance.

        Returns:
            True if CDC was stopped, False if not running
        """
        with self.lock:
            if instance_id not in self.registry:
                logger.warning(f"CDC not running for instance {instance_id}")
                return False

            try:
                cdc_service, thread, stop_event = self.registry[instance_id]

                # Signal shutdown
                stop_event.set()

                # Wait for thread to finish (with timeout)
                thread.join(timeout=10)

                if thread.is_alive():
                    logger.warning(f"CDC thread for instance {instance_id} did not stop gracefully")

                # Remove from registry
                del self.registry[instance_id]
                logger.info(f"Stopped CDC for instance {instance_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to stop CDC for instance {instance_id}: {e}")
                return False

    def start_all_enabled_cdc(self) -> int:
        """
        Start CDC for all database instances that have at least one
        sync definition with cdc_enabled=True.

        Returns:
            Number of CDC threads started
        """
        # Find all sync definitions with CDC enabled
        cdc_enabled_defs = self.db.execute(
            select(SyncDefinition).where(SyncDefinition.cdc_enabled == True)
        ).scalars().all()

        # Collect unique instance IDs from their primary sources
        instance_ids = set()
        for sync_def in cdc_enabled_defs:
            # Get primary source for this sync definition
            stmt = select(SyncSource).where(
                SyncSource.sync_def_id == sync_def.id,
                SyncSource.role == "PRIMARY"
            )
            source = self.db.execute(stmt).scalar_one_or_none()
            if source:
                instance_ids.add(source.database_instance_id)

        instance_ids = list(instance_ids)

        started_count = 0
        for instance_id in instance_ids:
            if self.start_cdc_for_instance(instance_id):
                started_count += 1

        logger.info(f"Started CDC for {started_count} database instances")
        return started_count

    def stop_all(self):
        """Stop all running CDC threads."""
        with self.lock:
            instance_ids = list(self.registry.keys())

        for instance_id in instance_ids:
            self.stop_cdc_for_instance(instance_id)

        logger.info("Stopped all CDC threads")

    def get_status(self) -> Dict[str, any]:
        """Get status of all running CDC threads."""
        with self.lock:
            return {
                "running_instances": len(self.registry),
                "instances": [
                    {
                        "instance_id": str(instance_id),
                        "thread_alive": thread.is_alive()
                    }
                    for instance_id, (_, thread, _) in self.registry.items()
                ]
            }
