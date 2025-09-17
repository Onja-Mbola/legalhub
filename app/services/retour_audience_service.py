import os
from typing import Optional
from datetime import datetime

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.retour_audience import RetourAudience
from app.repositories.dossier import get_dossier_by_id
from app.repositories.retour_audience import (
    get_retour_audience,
    get_retours_by_dossier,
    create_retour_audience,
    update_retour_audience)
from app.schemas.retour_audience import RetourAudienceCreate, RetourAudienceUpdate
from app.services.FileStorageService import save_uploaded_files
from app.services.workflow_guard import WorkflowGuard


def insert_or_update_retour_audience_with_file(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        date_audience: datetime,
        nom_judge: Optional[str],
        observations_judge: Optional[str],
        observations_internes: Optional[str],
        pv_audience: Optional[UploadFile],
        jugement_id: Optional[int] = None,
) -> RetourAudience:

    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage not in [ProcessStage.OPPOSITION.value, ProcessStage.RETOUR_AUDIENCE.value]:
        raise HTTPException(
            status_code=400,
            detail="Vous devez d'abord passer par l'Opposition ou être en Retour Audience pour enregistrer un retour."
        )

    dossier_path = os.path.join(
        "app/documents", avocat_nom, dossier.numero_dossier, "retour_audience"
    )

    retour_exist = get_retours_by_dossier(db, dossier_id)
    retour_exist = retour_exist[0] if retour_exist else None

    fichier_path = None
    if pv_audience and pv_audience.filename:
        saved_files = save_uploaded_files([pv_audience], dossier_path)
        fichier_path = os.path.join(dossier_path, saved_files[0])
    else:
        if retour_exist and retour_exist.pv_audience:
            fichier_path = retour_exist.pv_audience

    retour_in = RetourAudienceCreate(
        dossier_id=dossier_id,
        date_audience=date_audience,
        nom_judge=nom_judge,
        observations_judge=observations_judge,
        observations_internes=observations_internes,
        pv_audience=fichier_path,
        jugement_id=jugement_id,
    )

    if retour_exist:
        updated = update_retour_audience(
            db, retour_exist.id, RetourAudienceUpdate(**retour_in.dict(exclude={"dossier_id", "jugement_id"}))
        )
        return updated
    else:
        new = create_retour_audience(db, retour_in)
        WorkflowGuard.advance(dossier, ProcessStage.RETOUR_AUDIENCE, db)
        return new


def get_retour_audience_by_id(db: Session, retour_id: int):
    retour = get_retour_audience(db, retour_id)
    if not retour:
        raise HTTPException(status_code=404, detail="Retour audience non trouvé")
    return retour


def get_by_dossier(db: Session, dossier_id: int):
    return get_retours_by_dossier(db, dossier_id)
