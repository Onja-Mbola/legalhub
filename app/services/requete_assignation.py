import os
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.requete_assignation import RequeteAssignation
from app.repositories.dossier import get_dossier_by_id
from app.repositories.requete_assignation import create_requete_assignation, update_requete_assignation, \
    get_requete_assignation_by_dossier
from app.schemas.requete_assignation import RequeteAssignationCreate, RequeteAssignationUpdate
from app.services.FileStorageService import save_uploaded_files
from app.services.workflow_guard import WorkflowGuard


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

    dossier_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "requete_assignation")
    assignation_filename = None
    preuve_filename = None

    if assignation_file:
        assignation_filename = save_uploaded_files([assignation_file], dossier_path)[0]
    if preuve_signification_file:
        preuve_filename = save_uploaded_files([preuve_signification_file], dossier_path)[0]

    requete = create_requete_assignation(
        db, dossier_id, data, assignation_filename, preuve_filename
    )
    WorkflowGuard.advance(dossier, ProcessStage.REQUETE_ASSIGNATION, db)
    return requete


def update_requete_assignation_service(
        db: Session, db_obj, avocat_nom: str, dossier_id,
        data: RequeteAssignationUpdate,
        assignation_file: Optional[UploadFile] = None,
        preuve_signification_file: Optional[UploadFile] = None
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise Exception("Dossier non trouvé")
    dossier_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "requete_assignation")
    assignation_filename = None
    preuve_filename = None

    if assignation_file and assignation_file.filename:
        assignation_filename = save_uploaded_files([assignation_file], dossier_path)[0]
    if preuve_signification_file and preuve_signification_file.filename:
        preuve_filename = save_uploaded_files([preuve_signification_file], dossier_path)[0]

    return update_requete_assignation(
        db, db_obj, data, assignation_filename, preuve_filename
    )


def get_requete_assignation_by_dossier_service(db: Session, dossier_id: int) -> RequeteAssignation | None:
    return get_requete_assignation_by_dossier(db, dossier_id)
