import os
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.requete_assignation import RequeteAssignation
from app.models.dossier import Dossier
from app.repositories.dossier import get_dossier_by_id
from app.repositories.requete_assignation import create_requete_assignation, update_requete_assignation, \
    get_requete_assignation_by_dossier
from app.schemas.requete_assignation import RequeteAssignationCreate, RequeteAssignationUpdate
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload
from app.services.FileStorageService import storage


def create_requete_assignation_service(
        db: Session, dossier_id: int, avocat_nom: str,
        data: RequeteAssignationCreate,
        assignation_file: Optional[UploadFile] = None,
        preuve_signification_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.ENROLEMENT.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Enrolement.")

    requete = create_requete_assignation(
        db, dossier_id, data, None, None
    )
    db.commit()
    db.refresh(requete)

    has_assignation = assignation_file and assignation_file.filename
    if has_assignation:
        process_upload(
            obj=requete,
            files=[assignation_file],
            db=db,
            dossier=dossier,
            file_field="assignation_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder=""
        )
    else:
        process_upload(
            obj=requete,
            files=[],
            db=db,
            dossier=dossier,
            file_field="assignation_file",
            contenu_field="contenu",
            run_ml=True,
            subfolder=""
        )

    if preuve_signification_file and preuve_signification_file.filename:
        dossier_path = f"dossiers/{dossier.numero_dossier}/requeteassignations/preuve"
        preuve_paths = storage.save_uploaded_files([preuve_signification_file], dossier_path)
        requete.preuve_signification_file = preuve_paths[0]
        db.commit()
        db.refresh(requete)

    WorkflowGuard.advance(dossier, ProcessStage.REQUETE_ASSIGNATION, db)
    return requete


def update_requete_assignation_service(
        db: Session, db_obj: RequeteAssignation, avocat_nom: str, dossier_id: int,
        data: RequeteAssignationUpdate,
        assignation_file: Optional[UploadFile] = None,
        preuve_signification_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise Exception("Dossier non trouvé")

    obj = update_requete_assignation(
        db, db_obj, data, None, None
    )
    db.commit()
    db.refresh(obj)

    has_new_assignation = assignation_file and assignation_file.filename
    if has_new_assignation:
        process_upload(
            obj=obj,
            files=[assignation_file],
            db=db,
            dossier=dossier,
            file_field="assignation_file",
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,  # Re-ML
            subfolder=""
        )

    if preuve_signification_file and preuve_signification_file.filename:
        if obj.preuve_signification_file:
            storage.delete_object(obj.preuve_signification_file)
        dossier_path = f"dossiers/{dossier.numero_dossier}/requeteassignations/preuve"
        preuve_paths = storage.save_uploaded_files([preuve_signification_file], dossier_path)
        obj.preuve_signification_file = preuve_paths[0]
        db.commit()
        db.refresh(obj)

    return obj


def get_requete_assignation_by_dossier_service(db: Session, dossier_id: int) -> Optional[RequeteAssignation]:
    return get_requete_assignation_by_dossier(db, dossier_id)
