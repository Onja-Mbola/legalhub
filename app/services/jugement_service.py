import json
import os
from datetime import timedelta, datetime
from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.core.workflow_enums import ProcessStage
from app.db.session import SessionLocal
from app.models.jugement import Jugement
from app.models.dossier import Dossier  # NOUVEAU : Pour hook
from app.repositories.jugement import create_jugement, update_jugement, get_jugements_by_dossier, get_jugement_by_id
from app.schemas.jugement import JugementCreate, JugementUpdate
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.email import send_appel_email_programmer
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload
from app.services.FileStorageService import storage


def create_jugement_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: JugementCreate,
        user_id: int,
        jugement_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DECISION_DEFINITIVE.value:
        raise HTTPException(status_code=400, detail="Le jugement n'est accessible qu'après la décision définitive.")

    obj = create_jugement(db, data)
    # obj.jugement_file = None
    db.commit()
    db.refresh(obj)

    has_jugement = jugement_file and jugement_file.filename
    if has_jugement:
        process_upload(
            obj=obj,
            files=[jugement_file],
            db=db,
            dossier=dossier,
            file_field="fichier_jugement",
            contenu_field="texte_decision",
            ocr_all_files=False,
            run_ml=True,
            subfolder="favorable"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="fichier_jugement",
            contenu_field="texte_decision",
            run_ml=True,
            subfolder="favorable"
        )

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_FAVORABLE, db)

    log_action_service(db, user_id, "Création jugement favorable",
                       f"Création du jugement favorable pour le dossier {dossier.numero_dossier}",
                       dossier.id)

    return obj


def update_jugement_service(
        db: Session,
        jugement_id: int,
        avocat_nom: str,
        user_id: int,
        data: JugementUpdate,
        jugement_file: Optional[UploadFile] = None,
        scan_grosse: Optional[List[UploadFile]] = None
):
    existing = get_jugement_by_id(db, jugement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    dossier = existing.dossier

    updated = update_jugement(db, existing.id, data)
    db.commit()
    db.refresh(updated)

    has_new_jugement = jugement_file and jugement_file.filename
    if has_new_jugement:
        process_upload(
            obj=updated,
            files=[jugement_file],
            db=db,
            dossier=dossier,
            file_field="fichier_jugement",
            contenu_field="texte_decision",
            ocr_all_files=False,
            run_ml=True,
            subfolder="favorable"
        )

    if scan_grosse and any(f.filename for f in scan_grosse):
        if updated.scan_grosse:
            if isinstance(updated.scan_grosse, str):
                old_paths = json.loads(updated.scan_grosse)
            else:
                old_paths = updated.scan_grosse or []
            for old_path in old_paths:
                storage.delete_object(old_path)

        dossier_path = f"dossiers/{dossier.numero_dossier}/jugements/favorable/scan_grosse"
        new_paths = storage.save_uploaded_files(scan_grosse, dossier_path)
        updated.scan_grosse = new_paths
        db.commit()
        db.refresh(updated)

    # Log après
    log_action_service(db, user_id, "Mise à jour jugement",
                       f"Mise à jour du jugement pour le dossier {dossier.numero_dossier}",
                       dossier.id)

    return updated


def enregistrer_grosse_service(
        db: Session,
        jugement_id: int,
        avocat_nom: str,
        user_id: int,
        scan_grosse: List[UploadFile]
):
    jugement = get_jugement_by_id(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    dossier = jugement.dossier
    if dossier.current_stage != ProcessStage.NOTIFICATION_CLIENT.value:
        raise HTTPException(status_code=400, detail="La grosse ne peut être récupérée qu'après notification client")

    if jugement.scan_grosse:
        if isinstance(jugement.scan_grosse, str):
            old_paths = json.loads(jugement.scan_grosse)
        else:
            old_paths = jugement.scan_grosse or []
        for old_path in old_paths:
            storage.delete_object(old_path)

    dossier_path = f"dossiers/{dossier.numero_dossier}/jugements/favorable/scan_grosse"
    new_paths = storage.save_uploaded_files(scan_grosse, dossier_path)
    jugement.scan_grosse = new_paths  # List ou json.dumps si DB String
    db.commit()
    db.refresh(jugement)

    WorkflowGuard.advance(dossier, ProcessStage.RECUPERATION_GROSSE, db)

    log_action_service(db, user_id, "Récupération grosse",
                       f"Récupération de la grosse pour le dossier {dossier.numero_dossier}", dossier.id)

    return jugement


def archiver_jugement(db: Session, jugement_id: int, user_id: int):
    jugement = get_jugement_by_id_service(db, jugement_id)
    dossier = get_dossier_by_id_service(db, jugement.dossier_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement non trouvé")
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    if dossier.current_stage not in [ProcessStage.JUGEMENT_FAVORABLE.value, ProcessStage.RECUPERATION_GROSSE.value,
                                     ProcessStage.NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT]:
        raise HTTPException(status_code=400,
                            detail="L'archivage n'est accessible qu'après un jugement favorable ou notification client de jugement definitf ou défavorable ou Recuperation Grosse faite")

    jugement.statut = ProcessStage.FIN_ARCHIVAGE.value
    db.commit()
    db.refresh(jugement)
    WorkflowGuard.advance(dossier, ProcessStage.FIN_ARCHIVAGE, db)

    log_action_service(db, user_id, "Archivage jugement",
                       f"Archivage du jugement pour le dossier {dossier.numero_dossier}", dossier.id)

    return jugement


def get_jugement_by_id_service(db: Session, id: int):
    return get_jugement_by_id(db, id)


def get_jugement_by_dossier_service(db: Session, dossier_id: int):
    return get_jugements_by_dossier(db, dossier_id)


def create_jugement_defavorable_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: JugementCreate,
        user_id: int,
        jugement_file: Optional[UploadFile] = None,
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DECISION_DEFINITIVE.value:
        raise HTTPException(status_code=400,
                            detail="Le jugement défavorable n'est accessible qu'après la décision définitive.")


    obj = create_jugement(db, data)
    # obj.jugement_file = None
    db.commit()
    db.refresh(obj)

    has_jugement = jugement_file and jugement_file.filename
    if has_jugement:
        process_upload(
            obj=obj,
            files=[jugement_file],
            db=db,
            dossier=dossier,
            file_field="fichier_jugement",
            contenu_field="texte_decision",
            ocr_all_files=False,
            run_ml=True,
            subfolder="defavorable"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="fichier_jugement",
            contenu_field="texte_decision",
            run_ml=True,
            subfolder="defavorable"
        )

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_DEFAVORABLE, db)

    log_action_service(db, user_id, "Création jugement défavorable",
                       f"Création du jugement défavorable pour le dossier {dossier.numero_dossier}",
                       dossier.id)
    return obj


@celery_app.task()
def check_and_send_appel_alerts():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        jugements = db.query(Jugement).filter(Jugement.date_notification is not None).all()

        for jugement in jugements:
            if jugement.delai_appel and 15 <= jugement.delai_appel <= 30:
                date_limite = jugement.date_notification + timedelta(days=jugement.delai_appel)
                days_left = (date_limite - today).days

                if days_left == 5 and jugement.statut != "alerte_appel_envoyee":
                    try:
                        email_avocat = jugement.dossier.avocat_responsable_user.email
                        dossier_info = {
                            "nom_dossier": jugement.dossier.nom_dossier,
                            "numero_dossier": jugement.dossier.numero_dossier,
                            "date_notification": jugement.date_notification,
                            "date_limite": date_limite,
                            "days_left": days_left
                        }

                        send_appel_email_programmer.delay(
                            email=email_avocat,
                            dossier=dossier_info
                        )

                        jugement.statut = "alerte_appel_envoyee"
                        db.commit()

                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Erreur lors de l'envoi du mail pour le jugement {jugement.id} : {str(e)}"
                        )
    finally:
        db.close()


@celery_app.task()
def check_and_send_appel_alerts_1():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        jugements = db.query(Jugement).filter(Jugement.date_notification is not None).all()

        for jugement in jugements:
            date_limite = jugement.date_notification + timedelta(days=jugement.delai_appel)
            days_left = (date_limite - today).days

            if jugement.statut != "alerte_appel_envoyee":
                try:
                    email_avocat = jugement.dossier.avocat_responsable_user.email
                    dossier_info = {
                        "nom_dossier": jugement.dossier.nom_dossier,
                        "numero_dossier": jugement.dossier.numero_dossier,
                        "date_notification": jugement.date_notification,
                        "date_limite": date_limite,
                        "days_left": days_left
                    }

                    send_appel_email_programmer.delay(
                        email=email_avocat,
                        dossier=dossier_info
                    )

                    jugement.statut = "alerte_appel_envoyee"
                    db.commit()

                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erreur lors de l'envoi du mail pour le jugement {jugement.id} : {str(e)}"
                    )
    finally:
        db.close()
