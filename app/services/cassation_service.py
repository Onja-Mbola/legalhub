from datetime import timedelta, datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.core.workflow_enums import ProcessStage
from app.db.session import SessionLocal
from app.models.cassation import Cassation
from app.models.dossier import Dossier
from app.repositories.cassation import (
    create_cassation,
    get_cassation_by_id,
    get_cassation_by_decision_fond,
    get_cassations_by_dossier,
    get_all_cassations,
    get_cassations_by_statut,
    update_cassation,
    delete_cassation,
    get_cassations_with_pending_alerts
)
from app.repositories.dossier import get_dossier_by_id
from app.repositories.fond import get_decision_fond_by_id
from app.schemas.cassation import CassationCreate, CassationUpdate
from app.services.action_log import log_action_service
from app.services.workflow_guard import WorkflowGuard
from app.services.email import send_delai_alert_email
from app.services.FileStorageService import storage
from app.services.upload_processor import process_upload


def create_cassation_service(
        db: Session,
        data: CassationCreate,
        user_id: int,
        copie_requete: Optional[UploadFile] = None
) -> Cassation:
    decision_fond = get_decision_fond_by_id(db, data.decision_fond_id)
    if not decision_fond:
        raise HTTPException(status_code=404, detail="Décision de fond non trouvée")

    dossier = get_dossier_by_id(db, data.dossier_id)

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if decision_fond.type_decision_fond != "contradictoire":
        raise HTTPException(
            status_code=400,
            detail="La cassation n'est possible que pour les décisions contradictoires"
        )

    existing = get_cassation_by_decision_fond(db, data.decision_fond_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Une procédure de cassation existe déjà pour cette décision"
        )

    date_limite_cassation = data.date_notification_decision + timedelta(days=60)

    cassation_data = data.dict()
    cassation_data['date_limite_cassation'] = date_limite_cassation
    cassation_create = CassationCreate(**cassation_data)

    cassation = create_cassation(db, cassation_create)
    db.commit()
    db.refresh(cassation)

    has_requete = copie_requete and copie_requete.filename
    new_files = []
    if has_requete:
        dossier_path = f"dossiers/{dossier.numero_dossier}/cassations/cassation"
        new_paths = storage.save_uploaded_files([copie_requete], dossier_path)
        cassation.copie_requete = new_paths[0]
        new_files = [copie_requete]
        db.commit()
        db.refresh(cassation)

    if new_files:
        process_upload(
            obj=cassation,
            files=new_files,
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="observations",
            ocr_all_files=True,
            run_ml=True,
            subfolder="cassation"
        )
    else:
        process_upload(
            obj=cassation,
            files=[],
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="observations",
            run_ml=True,
            subfolder="cassation"
        )

    next_stage = ProcessStage.CASSATION
    WorkflowGuard.advance(dossier, next_stage, db)

    log_action_service(
        db, user_id,
        "Création cassation",
        f"Procédure de cassation créée pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return cassation


def get_cassation_service(db: Session, cassation_id: int) -> Cassation:
    cassation = get_cassation_by_id(db, cassation_id)
    if not cassation:
        raise HTTPException(status_code=404, detail="Cassation non trouvée")
    return cassation


def get_cassations_by_dossier_service(db: Session, dossier_id: int) -> List[Cassation]:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    return get_cassations_by_dossier(db, dossier_id)


def update_cassation_service(
        db: Session,
        cassation_id: int,
        data: CassationUpdate,
        user_id: int,
        copie_requete: Optional[UploadFile] = None,
        copie_memoire_ampliatif: Optional[UploadFile] = None,
        copie_memoire_defense: Optional[UploadFile] = None,
        copie_reponse: Optional[UploadFile] = None
) -> Cassation:
    cassation = get_cassation_by_id(db, cassation_id)
    if not cassation:
        raise HTTPException(status_code=404, detail="Cassation non trouvée")

    dossier = get_dossier_by_id(db, cassation.dossier_id)

    current_statut = cassation.statut

    def set_statut_if_not_done(new_statut: str):
        nonlocal current_statut
        ordre = ["en_attente_requete", "requete_deposee", "memoire_ampliatif_depose", "memoire_defense_recu",
                 "delibere"]
        if ordre.index(new_statut) > ordre.index(current_statut):
            current_statut = new_statut

    if data.date_depot_requete:
        data.date_limite_memoire_ampliatif = data.date_depot_requete + timedelta(days=60)
        if not data.statut:
            set_statut_if_not_done("requete_deposee")

    if data.date_depot_memoire_ampliatif and not data.statut:
        set_statut_if_not_done("memoire_ampliatif_depose")

    if data.date_reception_memoire_defense:
        data.date_limite_reponse = data.date_reception_memoire_defense + timedelta(days=10)
        if not data.statut:
            set_statut_if_not_done("memoire_defense_recu")

    if data.date_delibere:
        if not data.statut:
            set_statut_if_not_done("delibere")

    if data.date_depot_requete:
        date_notif = data.date_notification_decision or cassation.date_notification_decision
        if data.date_depot_requete < date_notif:
            raise HTTPException(
                status_code=400,
                detail="La date de dépôt de requête ne peut pas être antérieure à la date de notification"
            )

    data.statut = current_statut

    updated_cassation = update_cassation(db, cassation_id, data)
    db.commit()
    db.refresh(updated_cassation)

    new_files = []
    dossier_path = f"dossiers/{dossier.numero_dossier}/cassations/cassation"
    has_new_files = False

    if copie_requete and copie_requete.filename:
        new_paths = storage.save_uploaded_files([copie_requete], dossier_path)
        updated_cassation.copie_requete = new_paths[0]
        new_files.append(copie_requete)
        has_new_files = True

    if copie_memoire_ampliatif and copie_memoire_ampliatif.filename:
        new_paths = storage.save_uploaded_files([copie_memoire_ampliatif], dossier_path)
        updated_cassation.copie_memoire_ampliatif = new_paths[0]
        new_files.append(copie_memoire_ampliatif)
        has_new_files = True

    if copie_memoire_defense and copie_memoire_defense.filename:
        new_paths = storage.save_uploaded_files([copie_memoire_defense], dossier_path)
        updated_cassation.copie_memoire_defense = new_paths[0]
        new_files.append(copie_memoire_defense)
        has_new_files = True

    if copie_reponse and copie_reponse.filename:
        new_paths = storage.save_uploaded_files([copie_reponse], dossier_path)
        updated_cassation.copie_reponse = new_paths[0]
        new_files.append(copie_reponse)
        has_new_files = True

    if has_new_files:
        db.commit()
        db.refresh(updated_cassation)

    if has_new_files:
        process_upload(
            obj=updated_cassation,
            files=new_files,
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="observations",
            ocr_all_files=True,
            run_ml=True,
            subfolder="cassation"
        )

    log_action_service(
        db, user_id,
        "Mise à jour cassation",
        f"Procédure de cassation mise à jour pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return updated_cassation


def delete_cassation_service(db: Session, cassation_id: int, user_id: int) -> dict:
    cassation = get_cassation_by_id(db, cassation_id)
    if not cassation:
        raise HTTPException(status_code=404, detail="Cassation non trouvée")

    files_to_delete = [
        cassation.copie_requete,
        cassation.copie_memoire_ampliatif,
        cassation.copie_memoire_defense,
        cassation.copie_reponse
    ]
    for file_path in files_to_delete:
        if file_path:
            try:
                storage.delete_object(file_path)
                print(f"Fichier supprimé pour cassation {cassation_id}: {file_path}")
            except Exception as e:
                print(f"Erreur suppression fichier cassation {cassation_id}: {str(e)}")  # Non-blocant

    success = delete_cassation(db, cassation_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de la cassation"
        )

    return {"message": "Cassation supprimée avec succès", "id": cassation_id}


@celery_app.task()
def check_and_send_cassation_alerts():
    db = SessionLocal()
    try:
        cassations = get_cassations_with_pending_alerts(db)
        today = datetime.utcnow().date()

        for cassation in cassations:
            if not cassation.alerte_requete_envoyee and cassation.statut == "en_attente_requete":
                delta = cassation.date_limite_cassation - today
                if 0 <= delta.days <= 15:
                    try:
                        email_avocat = cassation.dossier.avocat_responsable_user.email if cassation.dossier and cassation.dossier.avocat_responsable_user else None
                        if email_avocat:
                            dossier_info = {
                                "nom_dossier": cassation.dossier.nom_dossier if cassation.dossier else "Inconnu",
                                "numero_dossier": cassation.dossier.numero_dossier if cassation.dossier else "Inconnu",
                                "type_alerte": "Dépôt requête en cassation",
                                "date_limite": cassation.date_limite_cassation,
                                "jours_restants": delta.days
                            }
                            send_delai_alert_email.delay(email=email_avocat, dossier=dossier_info)

                            update_data = CassationUpdate(alerte_requete_envoyee=True)
                            update_cassation(db, cassation.id, update_data)

                            print(f"Alerte requête envoyée pour cassation {cassation.id}")
                    except Exception as e:
                        print(f"Erreur alerte requête cassation {cassation.id}: {str(e)}")
                        db.rollback()

            if (not cassation.alerte_memoire_ampliatif_envoyee and
                    cassation.statut == "requete_deposee" and
                    cassation.date_depot_requete and
                    cassation.date_limite_memoire_ampliatif):

                delta = cassation.date_limite_memoire_ampliatif - today
                if 25 <= delta.days <= 35:
                    try:
                        email_avocat = cassation.dossier.avocat_responsable_user.email if cassation.dossier and cassation.dossier.avocat_responsable_user else None
                        if email_avocat:
                            dossier_info = {
                                "nom_dossier": cassation.dossier.nom_dossier if cassation.dossier else "Inconnu",
                                "numero_dossier": cassation.dossier.numero_dossier if cassation.dossier else "Inconnu",
                                "type_alerte": "Dépôt mémoire ampliatif",
                                "date_limite": cassation.date_limite_memoire_ampliatif,
                                "jours_restants": delta.days
                            }
                            send_delai_alert_email.delay(email=email_avocat, dossier=dossier_info)

                            update_data = CassationUpdate(alerte_memoire_ampliatif_envoyee=True)
                            update_cassation(db, cassation.id, update_data)

                            print(f"Alerte mémoire ampliatif envoyée pour cassation {cassation.id}")
                    except Exception as e:
                        print(f"Erreur alerte mémoire cassation {cassation.id}: {str(e)}")
                        db.rollback()

        db.commit()
    finally:
        db.close()
