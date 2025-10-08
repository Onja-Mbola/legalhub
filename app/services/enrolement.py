import os
from datetime import datetime
from typing import Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.enrolement import Enrolement
from app.repositories.dossier import get_dossier_by_id
from app.repositories.enrolement import get_enrolement_by_dossier, update_enrolement, create_enrolement, \
    get_enrolement_by_numero_role
from app.repositories.jugement import get_jugement_by_id
from app.schemas.enrolement import EnrolementCreate, EnrolementUpdate
from app.services.FileStorageService import storage
from app.services.workflow_guard import WorkflowGuard


def save_or_update_enrolement(
        db: Session,
        dossier_id: int,
        enrolement_in: EnrolementCreate
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=False)
    if enrolement:
        return update_enrolement(db, enrolement, EnrolementUpdate(**enrolement_in.dict()))
    else:
        if dossier.current_stage != ProcessStage.INTRODUCTION_INSTANCE.value:
            raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Introduction d'instance .")
        enrolement = create_enrolement(db, dossier_id, enrolement_in)
        WorkflowGuard.advance(dossier, ProcessStage.ENROLEMENT, db)
        return enrolement


def save_or_update_enrolement_appel(
        db: Session,
        dossier_id: int,
        enrolement_in: EnrolementCreate
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)
    if enrolement and enrolement.jugement_id is not None:
        return update_enrolement(db, enrolement, EnrolementUpdate(**enrolement_in.dict()))
    else:
        if dossier.current_stage != ProcessStage.APPEL.value:
            raise HTTPException(status_code=400, detail="Vous devez d'abord passer par l'Appel.")
        enrolement = create_enrolement(db, dossier_id, enrolement_in)
        WorkflowGuard.advance(dossier, ProcessStage.ENROLEMENT_APPEL, db)
        return enrolement


def insert_enrolement_with_file(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        numero_role: str,
        date_enrolement_str: str,
        frais_payes: Optional[float],
        greffier: Optional[str],
        preuve_enrolement_file: Optional[UploadFile]
) -> Enrolement:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    dossier_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "enrolement")

    enrolement_exist = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=False)

    fichier_path = None
    if preuve_enrolement_file and preuve_enrolement_file.filename:
        saved_files = storage.save_uploaded_files([preuve_enrolement_file], dossier_path)
        fichier_path = os.path.join(dossier_path, saved_files[0])
    else:
        if enrolement_exist and enrolement_exist.preuve_enrolement:
            fichier_path = enrolement_exist.preuve_enrolement

    try:
        date_enrolement = datetime.strptime(date_enrolement_str, "%Y-%m-%d").date()
    except ValueError:
        raise Exception("Format date invalide, attendu YYYY-MM-DD")

    enrolement_in = EnrolementCreate(
        numero_role=numero_role,
        date_enrolement=date_enrolement,
        frais_payes=frais_payes,
        greffier=greffier,
        preuve_enrolement=fichier_path,
    )

    enrolement = save_or_update_enrolement(db, dossier_id, enrolement_in)
    return enrolement


def insert_enrolement_appel_with_file(
        db: Session,
        dossier_id: int,
        jugement_id: int,
        avocat_nom: str,
        numero_role: str,
        date_enrolement_str: str,
        frais_payes: Optional[float],
        greffier: Optional[str],
        preuve_enrolement_file: Optional[UploadFile]
) -> Enrolement:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    jugement = get_jugement_by_id(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement non trouvé")

    dossier_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "enrolement_appel")

    enrolement_exist = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)

    fichier_path = None
    if preuve_enrolement_file and preuve_enrolement_file.filename:
        saved_files = storage.save_uploaded_files([preuve_enrolement_file], dossier_path)
        fichier_path = os.path.join(dossier_path, saved_files[0])
    else:
        if enrolement_exist and enrolement_exist.preuve_enrolement:
            fichier_path = enrolement_exist.preuve_enrolement

    try:
        date_enrolement = datetime.strptime(date_enrolement_str, "%Y-%m-%d").date()
    except ValueError:
        raise Exception("Format date invalide, attendu YYYY-MM-DD")

    enrolement_in = EnrolementCreate(
        numero_role=numero_role,
        date_enrolement=date_enrolement,
        frais_payes=frais_payes,
        greffier=greffier,
        preuve_enrolement=fichier_path,
        jugement_id=jugement.id
    )

    enrolement = save_or_update_enrolement_appel(db, dossier_id, enrolement_in)
    return enrolement


# def get_enrolement_by_dossier_service(db: Session, dossier_id: int) -> Enrolement | None:
#     return get_enrolement_by_dossier(db, dossier_id)

def get_enrolement_by_dossier_service(db: Session, dossier_id: int, with_jugement: bool = False) -> Optional[
    Enrolement]:
    enrolements = get_enrolement_by_dossier(db, dossier_id)
    if with_jugement:
        return next((e for e in enrolements if e.jugement_id is not None), None)
    else:
        return next((e for e in enrolements if e.jugement_id is None), None)


def get_enrolement_by_numero_role_service(db: Session, numero_role: int) -> int | None:
    return get_enrolement_by_numero_role(db, numero_role)
