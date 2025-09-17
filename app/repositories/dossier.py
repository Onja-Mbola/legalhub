import os
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.workflow_enums import ProcessStage
from app.models.adverse import Adverse
from app.models.client import Client
from app.models.demandeur import Demandeur
from app.models.dossier import Dossier
from app.schemas.dossier import DossierCreate
from app.services.FileStorageService import save_uploaded_files
from app.services.action_log import log_action_service


def get_next_numero_dossier(db: Session) -> str:
    last_dossier = db.query(Dossier).order_by(Dossier.id.desc()).first()
    next_id = 1 if not last_dossier else last_dossier.id + 1
    return f"DOS-{next_id}"


# def create_dossier(db: Session, dossier_in: DossierCreate, avocat_nom: str, user_id: int) -> Dossier:
#     client = Client(
#         adresse_client=dossier_in.client.adresse_client,
#         role_client=dossier_in.client.role_client
#     )
#
#     db.add(client)
#     db.flush()
#
#     for d in dossier_in.client.demandeurs:
#         db.add(Demandeur(client_id=client.id, **d.dict()))
#     for a in dossier_in.client.adverses:
#         db.add(Adverse(client_id=client.id, **a.dict()))
#
#     numero_dossier = get_next_numero_dossier(db)
#
#     dossier = Dossier(
#         numero_dossier=numero_dossier,
#         nom_dossier=dossier_in.nom_dossier,
#         type_affaire=dossier_in.type_affaire,
#         sous_type_affaire=dossier_in.sous_type_affaire,
#         urgence=dossier_in.urgence,
#         juridiction=dossier_in.juridiction,
#         tribunal=dossier_in.tribunal,
#         avocat_responsable=dossier_in.avocat_responsable,
#         avocat_adverse=dossier_in.avocat_adverse,
#         date_creation=dossier_in.date_creation,
#         commentaire=dossier_in.commentaire,
#         client_id=client.id,
#         dossier_path=f"uploads/{avocat_nom}/{numero_dossier}"
#     )
#
#     db.add(dossier)
#     db.commit()
#     db.refresh(dossier)
#
#     os.makedirs(dossier.dossier_path, exist_ok=True)
#
#     log_action_service(db, user_id, f"Création du dossier {dossier.numero_dossier}", dossier.id)
#
#     return dossier


def create_dossier_with_files(db: Session, dossier_in: DossierCreate, avocat_nom: str, files: List[UploadFile],
                              user_id: int) -> Dossier:
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

    log_action_service(db, user_id, "Création dossier", f"Création du dossier avec fichiers {dossier.numero_dossier}",
                       dossier.id)

    return dossier


def get_dossiers_by_avocat(db: Session, avocat_id: int):
    return (
        db.query(Dossier)
        .options(
            joinedload(Dossier.client).joinedload(Client.role_client_param),
            joinedload(Dossier.decisions_definitives),
            joinedload(Dossier.jugements),
            joinedload(Dossier.retours_audiences),
            joinedload(Dossier.deliberations_decisions)
        )
        .filter(Dossier.avocat_responsable == avocat_id)
        .all()
    )


def get_dossiers_archiver_by_avocat(db: Session, avocat_id: int):
    return (
        db.query(Dossier)
        .options(
            joinedload(Dossier.client).joinedload(Client.role_client_param)
        )
        .filter(Dossier.avocat_responsable == avocat_id,
                Dossier.current_stage == ProcessStage.FIN_ARCHIVAGE.value)
        .all()
    )


def get_dossier_by_id(db: Session, dossier_id: int):
    return (
        db.query(Dossier)
        .options(
            joinedload(Dossier.client).joinedload(Client.role_client_param),
            joinedload(Dossier.type_affaire_param),
            joinedload(Dossier.sous_type_affaire_param),
            joinedload(Dossier.urgence_param),
            joinedload(Dossier.users),
            joinedload(Dossier.enrolement),
            joinedload(Dossier.requete_assignation),
            joinedload(Dossier.premieres_audiences),
            joinedload(Dossier.echanges_conclusions),
            joinedload(Dossier.deliberations_decisions),
            joinedload(Dossier.decisions_avant_dire_droit),
            joinedload(Dossier.decisions_definitives),
            joinedload(Dossier.jugements),
            joinedload(Dossier.oppositions),
            joinedload(Dossier.retours_audiences),
            joinedload(Dossier.jugements_definitifs)
        )
        .filter(Dossier.id == dossier_id)
        .first()
    )


def update_dossier_with_files(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        nom_dossier: str,
        commentaire: str,
        files: List[UploadFile],
        user_id: int
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    dossier.nom_dossier = nom_dossier
    dossier.commentaire = commentaire

    pieces_jointes = dossier.pieces_jointes[:] if dossier.pieces_jointes else []
    dossier_path = dossier.dossier_path or os.path.join("app/documents", avocat_nom, dossier.numero_dossier)

    if files:
        files = [f for f in files if f.filename]
        if files:
            new_files = save_uploaded_files(files, dossier_path)
            pieces_jointes.extend(new_files)
            dossier.dossier_path = dossier_path

    dossier.pieces_jointes = pieces_jointes
    db.commit()
    db.refresh(dossier)

    log_action_service(db, user_id, f"Mise à jour du dossier {dossier.numero_dossier}", dossier.id)

    return dossier
