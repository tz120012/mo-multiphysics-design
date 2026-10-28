"""Optional Celery app (Q2-6 / Q3). Broker = REDIS_URL; degrades when Redis is down."""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "mo_api",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["app.tasks.analytic", "app.tasks.fem", "app.tasks.drive", "app.tasks.optimize"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    # Fail fast when broker is down so API can degrade to in-process path.
    broker_connection_retry_on_startup=True,
    broker_transport_options={"socket_timeout": 2, "socket_connect_timeout": 1},
    result_backend_transport_options={"socket_timeout": 2, "socket_connect_timeout": 1},
    # Ops compose worker-fem: celery -Q fem (docker-compose.yml)
    task_routes={
        "app.tasks.fem.run_fem_job": {"queue": "fem"},
        "app.tasks.optimize.run_optimize_job": {"queue": "optimize"},
    },
)
