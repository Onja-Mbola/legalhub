import os
from typing import Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage
from app.repositories.decision_avant_dire_droit import (
    create_decision_avant_dire_droit,
    update_decision_avant_dire_droit,
    get_decision_avant_dire_droit_by_dossier,
    get_decision_avant_dire_droit_by_id
)
from app.schemas.decision_avant_dire_droit import (
    DecisionAvantDireDroitCreate,
    DecisionAvantDireDroitUpdate
)
from app.services.dossier import get_dossier_by_id_service
from app.services.param_general import get_param
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload


def create_decision_avant_dire_droit_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: DecisionAvantDireDroitCreate,
        ordonnance_file: Optional[UploadFile] = None,
        retour_echange: bool = True
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DELIBERATION.value:
        raise HTTPException(
            status_code=400,
            detail="La décision avant dire droit n'est accessible qu'après la délibération."
        )

    existing_list = get_decision_avant_dire_droit_by_dossier(db, dossier_id)
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(status_code=400,
                            detail=f"Vous ne pouvez pas créer plus de {quota} décisions avant dire droit.")

    obj = create_decision_avant_dire_droit(db, data)
    # obj.ordonnance_file = None
    db.commit()
    db.refresh(obj)

    has_ordonnance = ordonnance_file and ordonnance_file.filename
    if has_ordonnance:
        process_upload(
            obj=obj,
            files=[ordonnance_file],
            db=db,
            dossier=dossier,
            file_field="ordonnance_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_avant_dire_droit"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="ordonnance_file",
            contenu_field="contenu",
            run_ml=True,
            subfolder="decision_avant_dire_droit"
        )

    next_stage = ProcessStage.DECISION_AVANT_DIRE_DROIT
    WorkflowGuard.advance(dossier, next_stage, db)
    return obj


def update_decision_avant_dire_droit_service(
        db: Session,
        decision_id: int,
        avocat_nom: str,
        data: DecisionAvantDireDroitUpdate,
        ordonnance_file: Optional[UploadFile] = None
):
    existing = get_decision_avant_dire_droit_by_id(db, decision_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Décision introuvable")

    dossier = existing.dossier

    updated = update_decision_avant_dire_droit(db, existing, data)
    db.commit()
    db.refresh(updated)

    has_new_ordonnance = ordonnance_file and ordonnance_file.filename
    if has_new_ordonnance:
        process_upload(
            obj=updated,
            files=[ordonnance_file],
            db=db,
            dossier=dossier,
            file_field="ordonnance_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_avant_dire_droit"
        )

    return updated


def get_decision_avant_dire_droit_by_id_service(db: Session, avant_dire_droit_id: int):
    return get_decision_avant_dire_droit_by_id(db, avant_dire_droit_id)


def get_decision_avant_dire_droit_by_dossier_service(db: Session, dossier_id: int):
    return get_decision_avant_dire_droit_by_dossier(db, dossier_id)
