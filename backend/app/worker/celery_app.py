import os
from celery import Celery

# Use env vars or defaults
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    db_user = os.environ.get("POSTGRES_USER", "change_me")
    db_password = os.environ.get("POSTGRES_PASSWORD", "change_me")
    db_host = os.environ.get("POSTGRES_HOST", "localhost")
    db_port = os.environ.get("POSTGRES_PORT", "5432")
    db_name = os.environ.get("POSTGRES_DB", "arcore_syncbridge")
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

celery_app = Celery(
    "arcore_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    task_routes={
        "app.worker.tasks.run_push_sync": {"queue": "sync_queue"},
        "app.worker.tasks.run_ingress_sync": {"queue": "sync_queue"},
        "app.worker.tasks.run_scheduled_sync": {"queue": "sync_queue"},
        "app.worker.tasks.reconcile_drift_metrics": {"queue": "default"},
        "app.worker.tasks.reconcile_single_sync": {"queue": "default"},
    },
    # Celery Beat Configuration
    beat_scheduler="celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler",
    beat_dburi=database_url,
    beat_schedule_filename="/tmp/celerybeat-schedule",  # Fallback for file-based scheduler
    beat_schedule={
        "reconcile-drift-metrics-every-30-minutes": {
            "task": "app.worker.tasks.reconcile_drift_metrics",
            "schedule": 1800.0,  # 30 minutes in seconds
            "options": {"queue": "default"}
        },
    },
)
