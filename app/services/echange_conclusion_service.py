import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage
from app.repositories.echange_conclusion import (
    create_echange_conclusion,
    update_echange_conclusion,
    get_echange_conclusion_by_dossier, get_echange_conclusion_by_id
)
from app.schemas.echange_conclusion import (
    EchangeConclusionCreate,
    EchangeConclusionUpdate
)
from app.services.param_general import get_param
from app.services.workflow_guard import WorkflowGuard
from app.services.FileStorageService import save_uploaded_files


def create_echange_conclusion_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: EchangeConclusionCreate,
        conclusions_file: Optional[UploadFile] = None
):
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.PREMIERE_AUDIENCE.value and dossier.current_stage != ProcessStage.DECISION_AVANT_DIRE_DROIT.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la Première audience.")

    existing_list = get_echange_conclusion_by_dossier(db, dossier_id)
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(
            status_code=400,
            detail=f"Vous ne pouvez pas créer plus de {quota} échanges de conclusion."
        )

    base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "echange_conclusions")
    file_path = None

    if conclusions_file and conclusions_file.filename:
        saved_files = save_uploaded_files([conclusions_file], base)
        file_path = os.path.join(base, saved_files[0])

    obj = create_echange_conclusion(db, data)
    if file_path:
        obj.conclusions_file = file_path
        db.commit()
        db.refresh(obj)

    WorkflowGuard.advance(dossier, ProcessStage.ECHANGE_CONCLUSIONS, db)

    return obj


def update_echange_conclusion_service(
        db: Session,
        echange_id: int,
        data: EchangeConclusionUpdate,
        conclusions_file: Optional[UploadFile] = None,
        avocat_nom: Optional[str] = None
):
    existing = get_echange_conclusion_by_id_service(db, echange_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Échange de conclusion non trouvé")

    dossier = db.query(Dossier).filter(Dossier.id == existing.dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier associé non trouvé")

    updated = update_echange_conclusion(db, existing, data)

    if conclusions_file and conclusions_file.filename and avocat_nom:
        base = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "echange_conclusions")
        saved_files = save_uploaded_files([conclusions_file], base)
        updated.conclusions_file = os.path.join(base, saved_files[0])
        db.commit()
        db.refresh(updated)

    return updated


def get_echange_conclusion_by_id_service(db: Session, id: int):
    return get_echange_conclusion_by_id(db, id)


def get_echange_conclusion_by_dossier_service(db: Session, dossier_id: int):
    return get_echange_conclusion_by_dossier(db, dossier_id)
