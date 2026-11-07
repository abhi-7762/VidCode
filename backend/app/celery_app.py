from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vidcode",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.script_tasks",
        "app.tasks.video_tasks",
        "app.tasks.render_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Fair scheduling for long tasks
    result_expires=86400,  # Results kept for 24h
)

