from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session, joinedload

from app.models.adverse import Adverse
from app.models.client import Client
from app.models.demandeur import Demandeur
from app.models.dossier import Dossier
from app.schemas.dossier import DossierCreate
import os


def get_next_numero_dossier(db: Session) -> str:
    last_dossier = db.query(Dossier).order_by(Dossier.id.desc()).first()
    next_id = 1 if not last_dossier else last_dossier.id + 1
    return f"DOS-{next_id}"


def create_dossier(db: Session, dossier_in: DossierCreate, avocat_nom: str) -> Dossier:
    client = Client(
        adresse_client=dossier_in.client.adresse_client,
        role_client=dossier_in.client.role_client
    )

    db.add(client)
    db.flush()

    for d in dossier_in.client.demandeurs:
        db.add(Demandeur(client_id=client.id, **d.dict()))
    for a in dossier_in.client.adverses:
        db.add(Adverse(client_id=client.id, **a.dict()))

    numero_dossier = get_next_numero_dossier(db)

    dossier = Dossier(
        numero_dossier=numero_dossier,
        nom_dossier=dossier_in.nom_dossier,
        type_affaire=dossier_in.type_affaire,
        sous_type_affaire=dossier_in.sous_type_affaire,
        urgence=dossier_in.urgence,
        juridiction=dossier_in.juridiction,
        tribunal=dossier_in.tribunal,
        avocat_responsable=dossier_in.avocat_responsable,
        avocat_adverse=dossier_in.avocat_adverse,
        date_creation=dossier_in.date_creation,
        commentaire=dossier_in.commentaire,
        client_id=client.id,
        dossier_path=f"uploads/{avocat_nom}/{numero_dossier}"
    )

    db.add(dossier)
    db.commit()
    db.refresh(dossier)

    os.makedirs(dossier.dossier_path, exist_ok=True)

    return dossier

def save_uploaded_files(files: List[UploadFile], dossier_path: str) -> List[str]:
    saved_files = []
    os.makedirs(dossier_path, exist_ok=True)
    for file in files:
        file_location = os.path.join(dossier_path, file.filename)
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        saved_files.append(file.filename)
    return saved_files


def create_dossier_with_files(db: Session, dossier_in: DossierCreate, avocat_nom: str, files: List[UploadFile]) -> Dossier:
    client = Client(
        adresse_client=dossier_in.client.adresse_client,
        role_client=dossier_in.client.role_client
    )
    db.add(client)
    db.flush()

    for d in dossier_in.client.demandeurs:
        db.add(Demandeur(client_id=client.id, **d.dict()))
    for a in dossier_in.client.adverses:
        db.add(Adverse(client_id=client.id, **a.dict()))

    numero_dossier = get_next_numero_dossier(db)
    dossier_path = os.path.join("app/documents", avocat_nom, numero_dossier)

    pieces_jointes = save_uploaded_files(files, dossier_path) if files else []

    dossier = Dossier(
        numero_dossier=numero_dossier,
        nom_dossier=dossier_in.nom_dossier,
        type_affaire=dossier_in.type_affaire,
        sous_type_affaire=dossier_in.sous_type_affaire,
        urgence=dossier_in.urgence,
        juridiction=dossier_in.juridiction,
        tribunal=dossier_in.tribunal,
        avocat_responsable=dossier_in.avocat_responsable,
        avocat_adverse=dossier_in.avocat_adverse,
        date_creation=dossier_in.date_creation,
        commentaire=dossier_in.commentaire,
        client_id=client.id,
        dossier_path=dossier_path,
        pieces_jointes=pieces_jointes
    )

    db.add(dossier)
    db.commit()
    db.refresh(dossier)
    return dossier

# def get_dossiers_by_avocat(db: Session, avocat_id: int):
#     return db.query(Dossier).filter(Dossier.avocat_responsable == avocat_id).all()

def get_dossiers_by_avocat(db: Session, avocat_id: int):
    return (
        db.query(Dossier)
        .options(
            joinedload(Dossier.client).joinedload(Client.role_client_param)
        )
        .filter(Dossier.avocat_responsable == avocat_id)
        .all()
    )


def get_dossier_by_id(db: Session, dossier_id: int):
    return (
            db.query(Dossier)
            .options(
                joinedload(Dossier.client).joinedload(Client.role_client_param)
            )
            .filter(Dossier.id == dossier_id)
            .first()
        )


def update_dossier_with_files(db: Session, dossier_id: int, nom_dossier: str, commentaire: str, files: List[UploadFile]):
    dossier = get_dossier_by_id(db, dossier_id)
    dossier.nom_dossier = nom_dossier
    dossier.commentaire = commentaire

    pieces_jointes = dossier.pieces_jointes or []

    if files:
        dossier_path = f"app/documents/{dossier.client.nom}/{dossier.numero_dossier}"
        os.makedirs(dossier_path, exist_ok=True)

        for file in files:
            file_path = os.path.join(dossier_path, file.filename)

            with open(file_path, "wb") as f:
                f.write(file.file.read())

            pieces_jointes.append({
                "filename": file.filename,
                "filepath": file_path
            })

    dossier.pieces_jointes = pieces_jointes

    db.commit()
    db.refresh(dossier)
    return dossier