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
from app.services.upload_processor import process_upload

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

    has_new_file = jugement_file and jugement_file.filename

    if existing:
        update_data = DecisionDefinitiveUpdate(**data.dict())
        existing = update_decision_definitive(db, existing, update_data)
        db.commit()
        db.refresh(existing)

        if has_new_file:
            process_upload(
                obj=existing,
                files=[jugement_file],
                db=db,
                dossier=dossier,
                file_field="jugement_file",
                contenu_field="contenu",
                ocr_all_files=False,
                run_ml=True,
                subfolder="decision_definitive"
            )

        return existing
    else:
        create_data = DecisionDefinitiveCreate(**data.dict())
        obj = create_decision_definitive(db, create_data)
        db.commit()
        db.refresh(obj)

        if has_new_file:
            process_upload(
                obj=obj,
                files=[jugement_file],
                db=db,
                dossier=dossier,
                file_field="jugement_file",
                contenu_field="contenu",
                ocr_all_files=False,
                run_ml=True,
                subfolder="decision_definitive"
            )
        else:
            process_upload(
                obj=obj,
                files=[],
                db=db,
                dossier=dossier,
                file_field="jugement_file",
                contenu_field="contenu",
                run_ml=True,
                subfolder="decision_definitive"
            )

        WorkflowGuard.advance(dossier, ProcessStage.DECISION_DEFINITIVE, db)
        return obj


def get_decision_definitive_by_id_service(db: Session, id: int):
    return get_decision_definitive_by_id(db, id)


def get_decision_definitive_by_dossier_service(db: Session, dossier_id: int):
    return get_decision_definitive_by_dossier(db, dossier_id)
