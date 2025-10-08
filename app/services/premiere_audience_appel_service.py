import os
from datetime import datetime
from typing import Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.premiere_audience_appel import PremiereAudienceAppel
from app.models.dossier import Dossier  # NOUVEAU : Pour hook
from app.repositories.dossier import get_dossier_by_id
from app.repositories.premiere_audience_appel import (
    get_premiere_audience_appel_by_dossier,
    create_premiere_audience_appel,
    update_premiere_audience_appel,
    get_premiere_audience_appel_by_id
)
from app.repositories.enrolement import get_enrolement_by_dossier
from app.schemas.premiere_audience_appel import (
    PremiereAudienceAppelCreate,
    PremiereAudienceAppelUpdate
)
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload  # NOUVEAU : Import hook


def save_or_update_premiere_audience_appel(
        db: Session,
        dossier_id: int,
        premiere_audience_appel_in: PremiereAudienceAppelCreate
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    premiere_audience_appel = get_premiere_audience_appel_by_dossier(db, dossier_id)

    if premiere_audience_appel:
        return update_premiere_audience_appel(
            db,
            premiere_audience_appel,
            PremiereAudienceAppelUpdate(**premiere_audience_appel_in.dict())
        )
    else:
        if dossier.current_stage != ProcessStage.ENROLEMENT_APPEL.value:
            raise HTTPException(
                status_code=400,
                detail="Vous devez d'abord passer par l'Enrôlement d'appel."
            )
        premiere_audience_appel = create_premiere_audience_appel(
            db,
            dossier_id,
            premiere_audience_appel_in
        )
        WorkflowGuard.advance(dossier, ProcessStage.PREMIERE_AUDIENCE_APPEL, db)
        return premiere_audience_appel


def insert_premiere_audience_appel_with_file(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        enrolement_appel_id: int,
        date_audience_str: str,
        heure_audience_str: Optional[str],
        lieu_audience: Optional[str],
        juge_rapporteur: Optional[str],
        observations: Optional[str],
        convocation_file: Optional[UploadFile]
) -> PremiereAudienceAppel:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    enrolements = get_enrolement_by_dossier(db, dossier_id)
    enrolement_appel = next((e for e in enrolements if e.jugement_id is not None), None)

    if not enrolement_appel or enrolement_appel.id != enrolement_appel_id:
        raise HTTPException(
            status_code=404,
            detail="Enrôlement d'appel non trouvé pour ce dossier"
        )

    premiere_audience_exist = get_premiere_audience_appel_by_dossier(db, dossier_id)

    has_new_file = convocation_file and convocation_file.filename

    try:
        date_audience = datetime.strptime(date_audience_str, "%Y-%m-%d").date()
    except ValueError:
        raise Exception("Format date invalide, attendu YYYY-MM-DD")

    heure_audience = None
    if heure_audience_str:
        try:
            heure_audience = datetime.strptime(heure_audience_str, "%H:%M").time()
        except ValueError:
            raise Exception("Format heure invalide, attendu HH:MM")

    premiere_audience_appel_in = PremiereAudienceAppelCreate(
        enrolement_appel_id=enrolement_appel_id,
        date_audience=date_audience,
        heure_audience=heure_audience,
        lieu_audience=lieu_audience,
        juge_rapporteur=juge_rapporteur,
        observations=observations,
        # convocation_recue=None
    )

    premiere_audience_appel = save_or_update_premiere_audience_appel(
        db,
        dossier_id,
        premiere_audience_appel_in
    )
    db.commit()
    db.refresh(premiere_audience_appel)

    if has_new_file:
        process_upload(
            obj=premiere_audience_appel,
            files=[convocation_file],
            db=db,
            dossier=dossier,
            file_field="convocation_recue",
            contenu_field="observations",
            ocr_all_files=False,
            run_ml=True,
            subfolder=""
        )
    else:
        process_upload(
            obj=premiere_audience_appel,
            files=[],
            db=db,
            dossier=dossier,
            file_field="convocation_recue",
            contenu_field="observations",
            run_ml=True,
            subfolder=""
        )

    return premiere_audience_appel


def get_premiere_audience_appel_by_dossier_service(
        db: Session,
        dossier_id: int
) -> Optional[PremiereAudienceAppel]:
    return get_premiere_audience_appel_by_dossier(db, dossier_id)


def get_premiere_audience_appel_by_id_service(
        db: Session,
        audience_id: int
) -> Optional[PremiereAudienceAppel]:
    return get_premiere_audience_appel_by_id(db, audience_id)
