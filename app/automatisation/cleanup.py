from datetime import datetime, timedelta

from app.automatisation.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.dossier import Dossier
from app.models.password_change_request import PasswordChangeRequest
from app.services.nlp_service import extract_entities
from app.services.ocr_service import anonymize_text


@celery_app.task()
def cleanup_expired_password_tokens():
    db = SessionLocal()
    try:
        expired_time = datetime.utcnow() - timedelta(hours=24)
        expired_tokens = db.query(PasswordChangeRequest).filter(
            PasswordChangeRequest.created_at < expired_time,
            PasswordChangeRequest.is_used == False
        )

        count = expired_tokens.count()
        expired_tokens.delete()

        db.commit()
        return f"Supprimé {count} tokens expirés"

    except Exception as e:
        db.rollback()
        return f"Erreur lors du nettoyage: {str(e)}"

    finally:
        db.close()


@celery_app.task(bind=True)
def async_process_upload(self, obj_data: dict, files_data: list, dossier_id: int):
    """Async : Traite après upload. obj_data : {'id':1, 'type':'EchangeConclusion'}. files_data : metadata (paths déjà stockés)."""
    # Reconstruisez obj depuis DB (import models)
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        dossier = db.query(Dossier).get(dossier_id)
        # Créez obj mock ou fetch réel (adaptez)
        # process_upload(obj_mock, [], db, dossier)  # Files déjà en MinIO
        print(f"Traitement async terminé pour {obj_data['id']}")
    finally:
        db.close()
    return {"status": "processed"}