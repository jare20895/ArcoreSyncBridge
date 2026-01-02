import os
from celery import Celery

# Use env vars or defaults
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

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
        # Future tasks
        # "app.worker.tasks.generate_drift_report": {"queue": "reports_queue"},
    }
)
