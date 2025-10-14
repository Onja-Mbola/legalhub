from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.enums import RoleEnum
from app.models.user import User
from app.models.dossier import Dossier
from app.schemas.dossier import DossierCreate
from app.repositories.dossier import (
    create_dossier_with_files,
    get_dossiers_by_avocat,
    get_dossier_by_id,
    update_dossier_with_files,
    get_dossiers_archiver_by_avocat,
    get_dossiers_for_clerk,
    get_dossiers_archiver_for_clerk
)


def create_new_dossier_with_files(db: Session, dossier_in: DossierCreate, avocat_nom: str, files: List[UploadFile],
                                  user_id: int):
    return create_dossier_with_files(db, dossier_in, avocat_nom, files, user_id)


def get_dossiers_by_user_service(db: Session, user: User, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    if user.role == RoleEnum.avocat:
        dossiers = get_dossiers_by_avocat(db, user.id)
    elif user.role == RoleEnum.clerk:
        if not user.created_by_id:
            return {"dossiers": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
        dossiers = get_dossiers_for_clerk(db, user)
    else:
        return {"dossiers": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}

    total = len(dossiers)
    offset = (page - 1) * per_page
    paginated_dossiers = dossiers[offset:offset + per_page]
    total_pages = (total + per_page - 1) // per_page

    return {
        "dossiers": paginated_dossiers,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


def get_dossiers_archiver_by_user_service(db: Session, user: User, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    if user.role == RoleEnum.avocat:
        dossiers = get_dossiers_archiver_by_avocat(db, user.id)
    elif user.role == RoleEnum.clerk:
        dossiers = get_dossiers_archiver_for_clerk(db, user)
    else:
        dossiers = []

    total = len(dossiers)
    offset = (page - 1) * per_page
    paginated_dossiers = dossiers[offset:offset + per_page]
    total_pages = (total + per_page - 1) // per_page

    return {
        "dossiers": paginated_dossiers,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


def get_all_dossiers_by_user_service(db: Session, user: User) -> List:
    if user.role == RoleEnum.avocat:
        return get_dossiers_by_avocat(db, user.id)
    elif user.role == RoleEnum.clerk:
        return get_dossiers_for_clerk(db, user)
    return []


def get_all_dossiers_archiver_by_user_service(db: Session, user: User) -> List:
    if user.role == RoleEnum.avocat:
        return get_dossiers_archiver_by_avocat(db, user.id)
    elif user.role == RoleEnum.clerk:
        return get_dossiers_archiver_for_clerk(db, user)
    return []


def get_dossiers_by_avocat_service(db: Session, avocat_id: int):
    return get_dossiers_by_avocat(db, avocat_id)


def get_dossiers_archiver_by_avocat_service(db: Session, avocat_id: int):
    return get_dossiers_archiver_by_avocat(db, avocat_id)


def get_dossier_by_id_service(db: Session, dossier_id: int):
    return get_dossier_by_id(db, dossier_id)


def update_dossier_with_files_service(db: Session, dossier_id: int, avocat_nom: str, nom_dossier: str,
                                      commentaire: str, consentement_rgpd: bool, files: List[UploadFile], user_id: int):
    return update_dossier_with_files(db, dossier_id, avocat_nom, nom_dossier, commentaire, consentement_rgpd, files,
                                     user_id)


def prepare_dossiers_for_export(dossiers: List) -> List[Dict[str, Any]]:
    export_data = []
    for d in dossiers:
        export_data.append({
            "Numéro": d.numero_dossier,
            "Nom du dossier": d.nom_dossier,
            "Type": d.type_affaire_param.valeur if d.type_affaire_param else "",
            "Sous-type": d.sous_type_affaire_param.valeur if d.sous_type_affaire_param else "",
            "Urgence": d.urgence_param.valeur if d.urgence_param else "",
            "Statut": d.current_stage or "",
            "Date création": d.date_creation.strftime('%d/%m/%Y') if d.date_creation else "",
            "Date archivage": d.date_archivage.strftime('%d/%m/%Y') if hasattr(d,
                                                                               'date_archivage') and d.date_archivage else ""
        })
    return export_data
