import os
from typing import Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.premiere_audience import PremiereAudience
from app.repositories.dossier import get_dossier_by_id
from app.repositories.premiere_audience import delete_premiere_audience
from app.repositories.premiere_audience import (
    get_premiere_audience,
    get_premieres_audiences_by_dossier,
    create_premiere_audience,
    update_premiere_audience
)
from app.schemas.premiere_audience import PremiereAudienceCreate, PremiereAudienceUpdate
from app.services.FileStorageService import save_uploaded_files
from app.services.workflow_guard import WorkflowGuard


def insert_or_update_premiere_audience_with_file(
    db: Session,
    dossier_id: int,
    avocat_nom: str,
    decision: str,
    nouvelle_date_audience: str,
    nom_judge: Optional[str],
    observations_judge: Optional[str],
    observations_internes: Optional[str],
    pv_audience: Optional[UploadFile]
) -> PremiereAudience:


    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.REQUETE_ASSIGNATION.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la Requête et l'Assignation.")

    dossier_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "premiere_audience")

    audience_exist = get_premieres_audiences_by_dossier(db, dossier_id)
    audience_exist = audience_exist[0] if audience_exist else None

    fichier_path = None
    if pv_audience and pv_audience.filename:
        saved_files = save_uploaded_files([pv_audience], dossier_path)
        fichier_path = os.path.join(dossier_path, saved_files[0])
    else:
        if audience_exist and audience_exist.pv_audience:
            fichier_path = audience_exist.pv_audience

    try:
        nouvelle_date_audience = nouvelle_date_audience
    except ValueError:
        raise Exception("Format date invalide, attendu YYYY-MM-DD")

    audience_in = PremiereAudienceCreate(
        nouvelle_date_audience=nouvelle_date_audience,
        decision=decision,
        nom_judge=nom_judge,
        observations_judge=observations_judge,
        observations_internes=observations_internes,
        pv_audience=fichier_path,
    )

    if audience_exist:
        updated = update_premiere_audience(db, audience_exist, PremiereAudienceUpdate(**audience_in.dict()))
        return updated
    else:
        new = create_premiere_audience(db, dossier_id, audience_in, pv_audience=fichier_path)
        WorkflowGuard.advance(dossier, ProcessStage.PREMIERE_AUDIENCE, db)
        return new


def get_premiere_audience_by_id(db: Session, audience_id: int):
    return get_premiere_audience(db, audience_id)


def get_by_dossier(db: Session, dossier_id: int):
    return get_premieres_audiences_by_dossier(db, dossier_id)


def delete(db: Session, audience_id: int):
    db_obj = get_premiere_audience(db, audience_id)
    if db_obj:
        delete_premiere_audience(db, db_obj)
        return True
    return False
