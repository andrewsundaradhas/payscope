from __future__ import annotations

from celery import Celery

from payscope_ingestion.config import Settings


def build_celery(settings: Settings) -> Celery:
    # We send tasks to the processing service worker queue.
    app = Celery("payscope_ingestion", broker=settings.celery_broker_url)
    app.conf.update(
        task_default_queue="processing",
        task_routes={"payscope_processing.tasks.parse_artifact": {"queue": "processing"}},
    )
    return app




