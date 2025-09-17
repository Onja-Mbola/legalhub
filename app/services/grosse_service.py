from fastapi_mail import FastMail
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.jugement import get_jugement_sans_grosse
from app.services.email import conf, send_jugement_favorable_email_programmer


@celery_app.task()
def check_grosse_rappel():
    db = SessionLocal()
    try:
        jugements = get_jugement_sans_grosse(db)

        for jugement in jugements:
            client_email = jugement.dossier.users.email
            if client_email:
                send_jugement_favorable_email_programmer.delay(client_email, jugement.dossier)
    finally:
        db.close()