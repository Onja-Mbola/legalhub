import os
from datetime import timedelta, datetime
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.automatisation import celery_app
from app.core.workflow_enums import ProcessStage
from app.repositories.jugement import create_jugement, update_jugement, get_jugements_by_dossier, get_jugement_by_id
from app.schemas.jugement import JugementCreate, JugementUpdate
from app.models.dossier import Dossier
from app.models.action_log import ActionLog
from app.services.FileStorageService import save_uploaded_files
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.email import send_jugement_favorable_email_programmer
from app.services.workflow_guard import WorkflowGuard


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

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "jugement_favorable")
    jugement_path = None

    if jugement_file and jugement_file.filename:
        saved_files = save_uploaded_files([jugement_file], base)
        jugement_path = os.path.join(base, saved_files[0])

    obj = create_jugement(db, data)
    if jugement_path:
        obj.jugement_file = jugement_path

    db.commit()
    db.refresh(obj)

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
        scan_grosse: Optional[list[UploadFile]] = None
):
    existing = get_jugement_by_id(db, jugement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    base = os.path.join("app/documents", avocat_nom, existing.dossier.numero_dossier, "jugement_favorable")
    jugement_path = None
    grosses_paths = []

    if jugement_file and jugement_file.filename:
        saved_files = save_uploaded_files([jugement_file], base)
        jugement_path = os.path.join(base, saved_files[0])

    if scan_grosse and any(f.filename for f in scan_grosse):
        saved_files = save_uploaded_files(scan_grosse, base)
        grosses_paths = [os.path.join(base, f) for f in saved_files]

    updated = update_jugement(db, existing.id, data)
    if jugement_path:
        updated.fichier_jugement = jugement_path
    if grosses_paths:
        updated.scan_grosse = grosses_paths

    db.commit()
    db.refresh(updated)

    log_action_service(db, user_id, "Mise à jour jugement", f"Mise à jour du jugement pour le dossier {existing.dossier.numero_dossier}",
                       existing.dossier.id)

    return updated


def enregistrer_grosse_service(
        db: Session,
        jugement_id: int,
        avocat_nom: str,
        user_id: int,
        scan_grosse: list[UploadFile]
):
    jugement = get_jugement_by_id(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    dossier = jugement.dossier
    if dossier.current_stage != ProcessStage.NOTIFICATION_CLIENT.value:
        raise HTTPException(status_code=400, detail="La grosse ne peut être récupérée qu'après notification client")

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "jugement_favorable", "scan_grosse")
    saved_files = save_uploaded_files(scan_grosse, base)
    jugement.scan_grosse = [os.path.join(base, f) for f in saved_files]

    db.commit()
    db.refresh(jugement)
    WorkflowGuard.advance(dossier, ProcessStage.RECUPERATION_GROSSE, db)

    log_action_service(db, user_id, "Récupération grosse", f"Récupération de la grosse pour le dossier {dossier.numero_dossier}", dossier.id)

    return jugement


def archiver_jugement(db: Session, jugement_id: int, user_id: int):
    jugement = get_jugement_by_id_service(db, jugement_id)
    dossier = get_dossier_by_id_service(db, jugement.dossier_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement non trouvé")
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    if dossier.current_stage not in [ProcessStage.JUGEMENT_FAVORABLE.value, ProcessStage.RECUPERATION_GROSSE.value, ProcessStage.NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT]:
        raise HTTPException(status_code=400,
                            detail="L'archivage n'est accessible qu'après un jugement favorable ou notification client de jugement definitf ou défavorable ou Recuperation Grosse faite")

    jugement.statut = ProcessStage.FIN_ARCHIVAGE.value
    db.commit()
    db.refresh(jugement)
    WorkflowGuard.advance(dossier, ProcessStage.FIN_ARCHIVAGE, db)

    log_action_service(db, user_id, "Archivage jugement", f"Archivage du jugement pour le dossier {dossier.numero_dossier}", dossier.id)

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

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "jugement_defavorable")
    jugement_path = None

    if jugement_file and jugement_file.filename:
        saved_files = save_uploaded_files([jugement_file], base)
        jugement_path = os.path.join(base, saved_files[0])

    obj = create_jugement(db, data)
    if jugement_path:
        obj.jugement_file = jugement_path

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_DEFAVORABLE, db)

    db.commit()
    db.refresh(obj)
    log_action_service(db, user_id, "Création jugement défavorable", f"Création du jugement défavorable pour le dossier {dossier.numero_dossier}",
                       dossier.id)
    return obj
