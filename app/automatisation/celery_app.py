import os
from datetime import timedelta

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
        "app.services.opposition_service",
        "app.services.jugement_service",
        "app.services.facture_service",
        "app.automatisation.cleanup",
        "app.services.fond_service",
        "app.services.cassation_service",
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
        "schedule": crontab(hour=9, minute=0),
    },
    "check_and_send_alerts": {
        "task": "app.services.opposition_service.check_and_send_alerts",
        "schedule": crontab(hour=9, minute=0),
    },
    "check_and_send_alerts_1": {
        "task": "app.services.opposition_service.check_and_send_alerts_1",
        "schedule": timedelta(minutes=1),
    },
    "check_and_send_appel_alerts": {
        "task": "app.services.jugement_service.check_and_send_appel_alerts",
        "schedule": crontab(hour=9, minute=0),
    },
    "check_and_send_appel_alerts_1": {
        "task": "app.services.jugement_service.check_and_send_appel_alerts_1",
        "schedule": timedelta(minutes=1),
    },
    "check_and_send_opposition_appel_alerts": {
        "task": "app.services.opposition_service.check_and_send_opposition_appel_alerts",
        "schedule": crontab(hour=9, minute=0),
    },
    "check_factures_rappel": {
        "task": "app.services.email.check_factures_rappel",
        "schedule": crontab(hour=9, minute=0),
    },
    "check_factures_rappel_hebdomadaire": {
        "task": "app.services.email.check_factures_rappel",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    "check_factures_rappel_fin_mois": {
        "task": "app.services.email.check_factures_rappel",
        "schedule": crontab(hour=9, minute=0, day_of_month=28),
    },
    "update_facture_status": {
        "task": "app.services.facture_service.update_facture_status_task",
        "schedule": crontab(hour=9, minute=0),
    },
    "cleanup-expired-password-tokens": {
        "task": "app.automatisation.cleanup.cleanup_expired_password_tokens",
        "schedule": crontab(hour=9, minute=0),
    },
    'check-fond-alerts-daily': {
        'task': 'app.services.fond_service.check_and_send_fond_alerts',
        'schedule': crontab(hour=9, minute=0),
    },
    'check_and_send_cassation_alerts': {
        'task': 'app.services.cassation_service.check_and_send_cassation_alerts',
        'schedule': crontab(hour=9, minute=0),
    }
}
