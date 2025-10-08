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
from app.services.upload_processor import process_upload


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

    obj = create_deliberation_decision(db, data)
    # obj.note_audience_file = None
    db.commit()
    db.refresh(obj)

    has_note = note_file and note_file.filename
    if has_note:
        process_upload(
            obj=obj,
            files=[note_file],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="deliberation_decision"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            run_ml=True,
            subfolder="deliberation_decision"
        )

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
        raise HTTPException(status_code=400,
                            detail="Vous devez d'abord passer par l'Échange de conclusions du jugement par defauts.")

    obj = create_deliberation_decision(db, data)
    db.commit()
    db.refresh(obj)

    has_note = note_file and note_file.filename
    if has_note:
        process_upload(
            obj=obj,
            files=[note_file],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="deliberation_decision_retour_audience"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            run_ml=True,
            subfolder="deliberation_decision_retour_audience"
        )

    WorkflowGuard.advance(dossier, ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT, db)
    return obj


def create_deliberation_decision_service_premiere_audience_appel(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: DeliberationDecisionCreate,
        note_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS_APPEL.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Échange de conclusions d'Appel.")

    obj = create_deliberation_decision(db, data)
    db.commit()
    db.refresh(obj)

    has_note = note_file and note_file.filename
    if has_note:
        process_upload(
            obj=obj,
            files=[note_file],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="deliberation_decision_premiere_audience_appel"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            run_ml=True,
            subfolder="deliberation_decision_premiere_audience_appel"
        )

    WorkflowGuard.advance(dossier, ProcessStage.DELIBERATION_APPEL, db)
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

    dossier = existing.dossier

    updated = update_deliberation_decision(db, existing, data)
    db.commit()
    db.refresh(updated)

    has_new_note = note_file and note_file.filename
    if has_new_note:
        process_upload(
            obj=updated,
            files=[note_file],
            db=db,
            dossier=dossier,
            file_field="note_audience_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="deliberation_decision"
        )

    return updated


def get_deliberation_decision_by_id_service(db: Session, decision_id: int):
    return get_deliberation_decision_by_id(db, decision_id)


def get_deliberation_decision_by_dossier_service(db: Session, dossier_id: int):
    return get_deliberation_decision_by_dossier(db, dossier_id)
