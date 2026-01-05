from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from croniter import croniter

from app.models.core import SyncDefinition, CeleryPeriodicTask


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def enable_schedule(
        self,
        sync_def_id: UUID,
        schedule_type: str,  # "INTERVAL" or "CRON"
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        timezone: str = "UTC"
    ):
        """
        Enable scheduled sync for a sync definition.
        Creates or updates CeleryPeriodicTask.
        """
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError("Sync definition not found")

        # Validate schedule
        if schedule_type == "INTERVAL":
            if not interval_seconds or interval_seconds < 60:
                raise ValueError("Interval must be at least 60 seconds")
        elif schedule_type == "CRON":
            if not cron_expression:
                raise ValueError("Cron expression required")
            # Validate cron
            try:
                croniter(cron_expression)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
        else:
            raise ValueError("schedule_type must be INTERVAL or CRON")

        # Update SyncDefinition
        sync_def.schedule_enabled = True
        sync_def.schedule_type = schedule_type
        sync_def.schedule_interval_seconds = interval_seconds
        sync_def.schedule_cron_expression = cron_expression
        sync_def.schedule_timezone = timezone
        sync_def.next_scheduled_run = self._calculate_next_run(
            schedule_type, interval_seconds, cron_expression, timezone
        )

        # Create or update CeleryPeriodicTask
        task_name = f"sync_def_{sync_def_id}_scheduled"
        stmt = select(CeleryPeriodicTask).where(CeleryPeriodicTask.name == task_name)
        periodic_task = self.db.execute(stmt).scalar_one_or_none()

        if not periodic_task:
            periodic_task = CeleryPeriodicTask(
                name=task_name,
                task="app.worker.tasks.run_scheduled_sync",
                sync_def_id=sync_def_id,
                args=[str(sync_def_id)],
                kwargs={},
                enabled=True
            )
            self.db.add(periodic_task)
        else:
            periodic_task.enabled = True
            periodic_task.sync_def_id = sync_def_id
            periodic_task.args = [str(sync_def_id)]

        # Set schedule based on type
        if schedule_type == "INTERVAL":
            periodic_task.interval_seconds = interval_seconds
            # Clear crontab fields
            periodic_task.crontab_minute = None
            periodic_task.crontab_hour = None
            periodic_task.crontab_day_of_week = None
            periodic_task.crontab_day_of_month = None
            periodic_task.crontab_month_of_year = None
        else:  # CRON
            # Parse cron expression (format: "minute hour day month day_of_week")
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Cron must have 5 parts: minute hour day month day_of_week")

            periodic_task.crontab_minute = parts[0]
            periodic_task.crontab_hour = parts[1]
            periodic_task.crontab_day_of_month = parts[2]
            periodic_task.crontab_month_of_year = parts[3]
            periodic_task.crontab_day_of_week = parts[4]
            periodic_task.interval_seconds = None

        periodic_task.date_changed = datetime.utcnow()

        self.db.commit()
        return {"message": "Schedule enabled", "next_run": sync_def.next_scheduled_run}

    def disable_schedule(self, sync_def_id: UUID):
        """Disable scheduled sync."""
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError("Sync definition not found")

        sync_def.schedule_enabled = False
        sync_def.next_scheduled_run = None

        # Disable periodic task
        task_name = f"sync_def_{sync_def_id}_scheduled"
        stmt = select(CeleryPeriodicTask).where(CeleryPeriodicTask.name == task_name)
        periodic_task = self.db.execute(stmt).scalar_one_or_none()

        if periodic_task:
            periodic_task.enabled = False
            periodic_task.date_changed = datetime.utcnow()

        self.db.commit()
        return {"message": "Schedule disabled"}

    def delete_schedule(self, sync_def_id: UUID):
        """Completely remove schedule."""
        self.disable_schedule(sync_def_id)

        task_name = f"sync_def_{sync_def_id}_scheduled"
        stmt = delete(CeleryPeriodicTask).where(CeleryPeriodicTask.name == task_name)
        self.db.execute(stmt)
        self.db.commit()
        return {"message": "Schedule deleted"}

    def _calculate_next_run(
        self,
        schedule_type: str,
        interval_seconds: Optional[int],
        cron_expression: Optional[str],
        timezone: str
    ) -> datetime:
        """Calculate next run time."""
        now = datetime.utcnow()

        if schedule_type == "INTERVAL":
            return now + timedelta(seconds=interval_seconds)
        else:  # CRON
            iter = croniter(cron_expression, now)
            return iter.get_next(datetime)
