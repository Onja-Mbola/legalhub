from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.schemas.dossier import DossierCreate
from app.repositories.dossier import create_dossier_with_files, get_dossiers_by_avocat, get_dossier_by_id, \
    update_dossier_with_files, get_dossiers_archiver_by_avocat


def create_new_dossier_with_files(db: Session, dossier_in: DossierCreate, avocat_nom: str, files: List[UploadFile],
                                  user_id: int):
    return create_dossier_with_files(db, dossier_in, avocat_nom, files, user_id)


def get_dossiers_by_avocat_service(db: Session, avocat_id: int):
    return get_dossiers_by_avocat(db, avocat_id)

def get_dossiers_archiver_by_avocat_service(db: Session, avocat_id: int):
    return get_dossiers_archiver_by_avocat(db, avocat_id)


def get_dossier_by_id_service(db: Session, dossier_id: int):
    return get_dossier_by_id(db, dossier_id)


def update_dossier_with_files_service(db: Session, dossier_id: int, avocat_nom: str, nom_dossier: str, commentaire: str,
                                      files: List[UploadFile], user_id: int):
    return update_dossier_with_files(db, dossier_id, avocat_nom, nom_dossier, commentaire, files, user_id)
