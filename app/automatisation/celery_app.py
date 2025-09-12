import os
from celery import Celery
from celery.schedules import crontab

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "legalhub",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.services.email",
        "app.services.grosse_service",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Nairobi",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check_grosse_rappel": {
        "task": "app.services.grosse_service.check_grosse_rappel",
        "schedule": crontab(hour=0, minute=0),
    },
    "check_and_send_alerts": {
        "task": "app.services.opposition_service.check_oppositions_rappel",
        "schedule": crontab(hour=0, minute=0),
    },
}
