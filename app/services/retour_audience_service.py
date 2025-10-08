import os
from typing import Optional
from datetime import datetime

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.retour_audience import RetourAudience
from app.models.dossier import Dossier
from app.repositories.dossier import get_dossier_by_id
from app.repositories.retour_audience import (
    get_retour_audience,
    get_retours_by_dossier,
    create_retour_audience,
    update_retour_audience)
from app.schemas.retour_audience import RetourAudienceCreate, RetourAudienceUpdate
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload


def insert_or_update_retour_audience_with_file(
        db: Session,
        dossier_id: int,
        avocat_nom: str,  # Gardé pour compat, mais pas utilisé dans paths (RGPD)
        date_audience: datetime,
        nom_judge: Optional[str],
        observations_judge: Optional[str],
        observations_internes: Optional[str],
        pv_audience: Optional[UploadFile],  # Fichier unique
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

    # SUPPRIME : dossier_path et MinIO manuel (déplacé dans hook)

    retour_exist = get_retours_by_dossier(db, dossier_id)
    retour_exist = retour_exist[0] if retour_exist else None

    # Préparez data sans fichier (pour repo)
    retour_in = RetourAudienceCreate(
        dossier_id=dossier_id,
        date_audience=date_audience,
        nom_judge=nom_judge,
        observations_judge=observations_judge,
        observations_internes=observations_internes,
        # pv_audience=None  # Sera set par hook (String ou JSON)
        jugement_id=jugement_id,
    )

    has_new_file = pv_audience and pv_audience.filename  # Check si nouveau fichier

    if retour_exist:
        # UPDATE : Update basique d'abord
        updated = update_retour_audience(
            db, retour_exist.id, RetourAudienceUpdate(**retour_in.dict(exclude={"dossier_id", "jugement_id"}))
        )
        db.commit()  # Commit initial (sans fichier)
        db.refresh(updated)

        if has_new_file:
            process_upload(
                obj=updated,
                files=[pv_audience],
                db=db,
                dossier=dossier,
                file_field="pv_audience",
                contenu_field="observations_judge",
                ocr_all_files=False,
                run_ml=True,
                subfolder=""
            )

        return updated
    else:
        new = create_retour_audience(db, retour_in)
        db.commit()
        db.refresh(new)

        if has_new_file:
            process_upload(
                obj=new,
                files=[pv_audience],
                db=db,
                dossier=dossier,
                file_field="pv_audience",
                contenu_field="observations_judge",
                ocr_all_files=False,
                run_ml=True,
                subfolder=""
            )
        else:
            process_upload(
                obj=new,
                files=[],
                db=db,
                dossier=dossier,
                file_field="pv_audience",
                contenu_field="observations_judge",
                run_ml=True,
                subfolder=""
            )

        WorkflowGuard.advance(dossier, ProcessStage.RETOUR_AUDIENCE, db)
        return new


def get_retour_audience_by_id(db: Session, retour_id: int):
    retour = get_retour_audience(db, retour_id)
    if not retour:
        raise HTTPException(status_code=404, detail="Retour audience non trouvé")
    return retour


def get_by_dossier(db: Session, dossier_id: int):
    return get_retours_by_dossier(db, dossier_id)
