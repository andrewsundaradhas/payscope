from __future__ import annotations

from celery import Celery

from payscope_processing.config import get_settings


def make_celery() -> Celery:
    settings = get_settings()
    app = Celery("payscope_processing", broker=settings.celery_broker_url)
    app.conf.update(
        task_default_queue="processing",
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )
    app.autodiscover_tasks(["payscope_processing"])
    return app


celery_app = make_celery()




