from typing import Optional, List

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.repositories.echange_conclusion import (
    create_echange_conclusion,
    update_echange_conclusion,
    get_echange_conclusion_by_dossier, get_echange_conclusion_by_id, get_echanges_by_retour, delete_echange_conclusion
)
from app.schemas.echange_conclusion import (
    EchangeConclusionCreate,
    EchangeConclusionUpdate
)
from app.services.dossier import get_dossier_by_id_service
from app.services.param_general import get_param
from app.services.upload_processor import process_upload
from app.services.workflow_guard import WorkflowGuard


def create_echange_conclusion_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: EchangeConclusionCreate,
        conclusions_file: List[UploadFile]
):
    stages_autorises = [
        ProcessStage.PREMIERE_AUDIENCE.value,
        ProcessStage.DECISION_AVANT_DIRE_DROIT.value,
        ProcessStage.ECHANGE_CONCLUSIONS.value
    ]
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage not in stages_autorises:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la Première audience.")

    existing_list = get_echange_conclusion_by_dossier_service(db, dossier_id)
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(
            status_code=400,
            detail=f"Vous ne pouvez pas créer plus de {quota} échanges de conclusion."
        )

    obj = create_echange_conclusion(db, data)
    db.commit()
    db.refresh(obj)

    has_files = conclusions_file and any(f.filename.strip() for f in conclusions_file)
    if has_files:
        process_upload(
            obj=obj,
            files=conclusions_file,
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            ocr_all_files=False,
            run_ml=True,
            subfolder=""
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            run_ml=True,
            subfolder=""
        )

    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS.value:
        WorkflowGuard.advance(dossier, ProcessStage.ECHANGE_CONCLUSIONS, db)

    return obj


def create_echange_conclusion_service_retour_audience(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: EchangeConclusionCreate,
        conclusions_file: List[UploadFile]
):
    stages_autorises = [
        ProcessStage.RETOUR_AUDIENCE.value,
        ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT.value
    ]
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage not in stages_autorises:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la Retour d'audience.")

    existing_list = get_echange_conclusion_by_dossier_service(db, dossier_id, arg="retour")
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(
            status_code=400,
            detail=f"Vous ne pouvez pas créer plus de {quota} échanges de conclusion."
        )

    obj = create_echange_conclusion(db, data)
    db.commit()
    db.refresh(obj)

    has_files = conclusions_file and any(f.filename.strip() for f in conclusions_file)
    if has_files:
        process_upload(
            obj=obj,
            files=conclusions_file,
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            ocr_all_files=False,
            run_ml=True,
            subfolder="par_defaut"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            run_ml=True,
            subfolder="par_defaut"
        )

    # Workflow
    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT.value:
        WorkflowGuard.advance(dossier, ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT, db)

    return obj


def create_echange_conclusion_service_premiere_appel(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: EchangeConclusionCreate,
        conclusions_file: List[UploadFile]
):
    stages_autorises = [
        ProcessStage.PREMIERE_AUDIENCE_APPEL.value,
        ProcessStage.ECHANGE_CONCLUSIONS_APPEL.value,
        ProcessStage.AVANT_DIRE_DROIT.value
    ]
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage not in stages_autorises:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la Premiere Appel.")

    existing_list = get_echange_conclusion_by_dossier_service(db, dossier_id, arg="appel")
    quota = int(get_param(db, "quota_echange_conclusion_civil").valeur)
    if len(existing_list) >= quota:
        raise HTTPException(
            status_code=400,
            detail=f"Vous ne pouvez pas créer plus de {quota} échanges de conclusion."
        )

    obj = create_echange_conclusion(db, data)
    db.commit()
    db.refresh(obj)

    has_files = conclusions_file and any(f.filename.strip() for f in conclusions_file)
    if has_files:
        process_upload(
            obj=obj,
            files=conclusions_file,
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            ocr_all_files=False,
            run_ml=True,
            subfolder="premiere_appel"
        )
    else:
        process_upload(
            obj=obj,
            files=[],
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            run_ml=True,
            subfolder="premiere_appel"
        )

    # Workflow
    if dossier.current_stage != ProcessStage.ECHANGE_CONCLUSIONS_APPEL.value:
        WorkflowGuard.advance(dossier, ProcessStage.ECHANGE_CONCLUSIONS_APPEL, db)

    return obj


def update_echange_conclusion_service(
        db: Session,
        echange_id: int,
        data: EchangeConclusionUpdate,
        conclusions_file: Optional[List[UploadFile]] = None,
        avocat_nom: Optional[str] = None
):
    existing = get_echange_conclusion_by_id_service(db, echange_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Échange de conclusion non trouvé")

    dossier = get_dossier_by_id_service(db, existing.dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier associé non trouvé")

    updated = update_echange_conclusion(db, existing, data)
    db.commit()
    db.refresh(updated)

    has_new_files = conclusions_file and any(f.filename.strip() for f in conclusions_file or [])
    if has_new_files:
        process_upload(
            obj=updated,
            files=conclusions_file,
            db=db,
            dossier=dossier,
            file_field="conclusions_file",
            contenu_field="contenu_resume",
            ocr_all_files=False,
            run_ml=True,
            subfolder=""
        )

    return updated


def get_echange_conclusion_by_id_service(db: Session, id: int):
    return get_echange_conclusion_by_id(db, id)


# def get_echange_conclusion_by_dossier_service(db: Session, dossier_id: int):
#     return get_echange_conclusion_by_dossier(db, dossier_id)


def get_echange_conclusion_by_dossier_service(db: Session, dossier_id: int, arg: Optional[str] = None):
    echanges = get_echange_conclusion_by_dossier(db, dossier_id)

    if arg == "retour":
        return [e for e in echanges if e.retour_audience_id is not None]
    elif arg == "appel":
        return [e for e in echanges if e.premiere_appel_id is not None]
    elif arg is None:
        return [e for e in echanges if e.retour_audience_id is None and e.premiere_appel_id is None]

    return []


def get_echanges_by_retour_service(db: Session, retour_audience_id: int):
    return get_echanges_by_retour(db, retour_audience_id)


def delete_echange_conclusion_service(db: Session, echange_id: int):
    return delete_echange_conclusion(db, echange_id)
