import os
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.repositories.jugement_definitif import (
    create_jugement_definitif,
    update_jugement_definitif,
    get_jugement_definitif,
    get_jugements_definitifs_by_dossier,
)
from app.schemas.jugement_definitif import JugementDefinitifCreate, JugementDefinitifUpdate
from app.models.dossier import Dossier
from app.services.FileStorageService import save_uploaded_files
from app.services.dossier import get_dossier_by_id_service
from app.services.action_log import log_action_service
from app.services.workflow_guard import WorkflowGuard


def create_jugement_definitif_service(
    db: Session,
    dossier_id: int,
    avocat_nom: str,
    data: JugementDefinitifCreate,
    user_id: int,
    fichiers: Optional[List[UploadFile]] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT.value:
        raise HTTPException(
            status_code=400,
            detail="Le jugement définitif n'est accessible qu'après la deliberation"
        )

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "jugement_definitif")
    fichiers_paths = []

    if fichiers and any(f.filename for f in fichiers):
        saved_files = save_uploaded_files(fichiers, base)
        fichiers_paths = [os.path.join(base, f) for f in saved_files]

    obj = create_jugement_definitif(db, data)
    if fichiers_paths:
        obj.jugement_file = fichiers_paths

    db.commit()
    db.refresh(obj)

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_DEFINITIF, db)

    log_action_service(
        db,
        user_id,
        "Création jugement définitif",
        f"Création du jugement définitif pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return obj


def update_jugement_definitif_service(
    db: Session,
    jugement_id: int,
    avocat_nom: str,
    user_id: int,
    data: JugementDefinitifUpdate,
    fichiers: Optional[List[UploadFile]] = None
):
    existing = get_jugement_definitif(db, jugement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Jugement définitif introuvable")

    base = os.path.join("app/documents", avocat_nom, existing.dossier.numero_dossier, "jugement_definitif")
    fichiers_paths = []

    if fichiers and any(f.filename for f in fichiers):
        saved_files = save_uploaded_files(fichiers, base)
        fichiers_paths = [os.path.join(base, f) for f in saved_files]

    updated = update_jugement_definitif(db, existing, data)
    if fichiers_paths:
        updated.jugement_file = fichiers_paths

    db.commit()
    db.refresh(updated)

    log_action_service(
        db,
        user_id,
        "Mise à jour jugement définitif",
        f"Mise à jour du jugement définitif pour le dossier {existing.dossier.numero_dossier}",
        existing.dossier.id
    )

    return updated


def get_jugement_definitif_by_id_service(db: Session, id: int):
    return get_jugement_definitif(db, id)


def get_jugements_definitifs_by_dossier_service(db: Session, dossier_id: int):
    return get_jugements_definitifs_by_dossier(db, dossier_id)
