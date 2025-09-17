import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage
from app.repositories.decision_definitive import (
    create_decision_definitive,
    update_decision_definitive,
    get_decision_definitive_by_dossier, get_decision_definitive_by_id
)
from app.schemas.decision_definitive import (
    DecisionDefinitiveCreate,
    DecisionDefinitiveUpdate
)
from app.services.dossier import get_dossier_by_id_service
from app.services.workflow_guard import WorkflowGuard
from app.services.FileStorageService import save_uploaded_files


def save_or_update_decision_definitive(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: DecisionDefinitiveCreate,
        jugement_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage not in [ProcessStage.DELIBERATION.value, ProcessStage.DECISION_DEFINITIVE.value]:
        raise HTTPException(
            status_code=400,
            detail="La décision définitive n'est accessible qu'après la délibération."
        )

    existing = get_decision_definitive_by_dossier(db, dossier_id)

    base = os.path.join("app/documents", str(avocat_nom), str(dossier.numero_dossier), "decision_definitive")
    file_path = None

    if jugement_file and jugement_file.filename:
        saved_files = save_uploaded_files([jugement_file], base)
        file_path = os.path.join(base, saved_files[0])
    elif existing:
        file_path = existing.jugement_file

    if existing:
        update_data = DecisionDefinitiveUpdate(**data.dict())
        existing = update_decision_definitive(db, existing, update_data)
        existing.jugement_file = file_path
        db.commit()
        db.refresh(existing)
        return existing
    else:
        if existing is not None:
            raise HTTPException(
                status_code=400,
                detail="Une décision définitive existe déjà pour ce dossier."
            )

        create_data = DecisionDefinitiveCreate(**data.dict())
        obj = create_decision_definitive(db, create_data)
        obj.jugement_file = file_path
        db.commit()
        db.refresh(obj)
        WorkflowGuard.advance(dossier, ProcessStage.DECISION_DEFINITIVE, db)
        return obj


def get_decision_definitive_by_id_service(db: Session, id: int):
    return get_decision_definitive_by_id(db, id)


def get_decision_definitive_by_dossier_service(db: Session, dossier_id: int):
    return get_decision_definitive_by_dossier(db, dossier_id)
