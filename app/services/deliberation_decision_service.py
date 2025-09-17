import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage
from app.repositories.deliberation_decision import (
    create_deliberation_decision,
    update_deliberation_decision,
    get_deliberation_decision_by_dossier,
    get_deliberation_decision_by_id
)
from app.schemas.deliberation_decision import (
    DeliberationDecisionCreate,
    DeliberationDecisionUpdate
)
from app.services.dossier import get_dossier_by_id_service
from app.services.param_general import get_param
from app.services.workflow_guard import WorkflowGuard
from app.services.FileStorageService import save_uploaded_files


def create_deliberation_decision_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: DeliberationDecisionCreate,
        note_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Échange de conclusions.")

    existing_list = get_deliberation_decision_by_dossier(db, dossier_id)
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(status_code=400, detail=f"Vous ne pouvez pas créer plus de {quota} délibérations.")

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "deliberation_decision")
    file_path = None
    if note_file and note_file.filename:
        saved_files = save_uploaded_files([note_file], base)
        file_path = os.path.join(base, saved_files[0])

    obj = create_deliberation_decision(db, data)
    if file_path:
        obj.note_audience_file = file_path
        db.commit()
        db.refresh(obj)

    WorkflowGuard.advance(dossier, ProcessStage.DELIBERATION, db)
    return obj


def create_deliberation_decision_service_retour_audience(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: DeliberationDecisionCreate,
        note_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Échange de conclusions du jugement par defauts.")

    existing_list = get_deliberation_decision_by_dossier(db, dossier_id)
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(status_code=400, detail=f"Vous ne pouvez pas créer plus de {quota} délibérations.")

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "deliberation_decision")
    file_path = None
    if note_file and note_file.filename:
        saved_files = save_uploaded_files([note_file], base)
        file_path = os.path.join(base, saved_files[0])

    obj = create_deliberation_decision(db, data)
    if file_path:
        obj.note_audience_file = file_path
        db.commit()
        db.refresh(obj)

    WorkflowGuard.advance(dossier, ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT, db)
    return obj


def update_deliberation_decision_service(
        db: Session,
        decision_id: int,
        avocat_nom: str,
        data: DeliberationDecisionUpdate,
        note_file: Optional[UploadFile] = None
):
    existing = get_deliberation_decision_by_id(db, decision_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Délibération introuvable")

    base = os.path.join("app/documents", avocat_nom, existing.dossier.numero_dossier,
                        "deliberation_decision")
    file_path = None
    if note_file and note_file.filename:
        saved_files = save_uploaded_files([note_file], base)
        file_path = os.path.join(base, saved_files[0])

    updated = update_deliberation_decision(db, existing, data)
    if file_path:
        updated.note_audience_file = file_path
        db.commit()
        db.refresh(updated)

    return updated


def get_deliberation_decision_by_id_service(db: Session, id: int):
    return get_deliberation_decision_by_id(db, id)


def get_deliberation_decision_by_dossier_service(db: Session, dossier_id: int):
    return get_deliberation_decision_by_dossier(db, dossier_id)
