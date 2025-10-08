from datetime import timedelta, datetime
from typing import List, Type, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.core.workflow_enums import ProcessStage
from app.db.session import SessionLocal
from app.models.fond import Fond
from app.repositories.dossier import get_dossier_by_id
from app.repositories.fond import (
    create_decision_fond,
    get_decision_fond_by_id,
    get_decisions_fond_by_dossier,
    get_decisions_fond_by_deliberation,
    get_decisions_fond_par_defaut,
    get_decisions_fond_contradictoires,
    update_decision_fond,
    delete_decision_fond,
    get_all_decisions_fond_with_alerts_pending
)
from app.schemas.fond import DecisionFondCreate, DecisionFondUpdate
from app.services.action_log import log_action_service
from app.services.opposition_service import create_opposition_appel_auto
from app.services.upload_processor import process_upload
from app.services.workflow_guard import WorkflowGuard
from app.services.email import send_delai_alert_email


def create_decision_fond_service(db: Session, data: DecisionFondCreate, user_id: int, copie_decision_fond: Optional[UploadFile] = None) -> Fond:
    dossier = get_dossier_by_id(db, data.dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DELIBERATION_APPEL.value:
        raise HTTPException(
            status_code=400,
            detail="La décision de fond n'est accessible qu'après la délibération."
        )

    if data.date_notification:
        if data.date_notification < data.date_decision_fond:
            raise HTTPException(
                status_code=400,
                detail="La date de notification ne peut pas être antérieure à la date de décision"
            )

    date_limite_appel = None
    if data.date_notification:
        date_limite_appel = data.date_notification + timedelta(days=data.delai_appel)

    decision_data = data.dict()
    decision_data['date_limite_appel'] = date_limite_appel
    decision_fond_create = DecisionFondCreate(**decision_data)

    decision_fond = create_decision_fond(db, decision_fond_create)

    has_file = copie_decision_fond and copie_decision_fond.filename
    if has_file:
        process_upload(
            obj=decision_fond,
            files=[copie_decision_fond],
            db=db,
            dossier=dossier,
            file_field="copie_decision_fond",
            contenu_field="observations",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_fond"
        )
    else:
        process_upload(
            obj=decision_fond,
            files=[],
            db=db,
            dossier=dossier,
            file_field="copie_decision_fond",
            contenu_field="observations",
            run_ml=True,
            subfolder="decision_fond"
        )

    if data.type_decision_fond == "par_defaut" and data.date_notification:
        create_opposition_appel_auto(db, decision_fond.id, data.date_notification)

    next_stage = ProcessStage.FOND
    WorkflowGuard.advance(dossier, next_stage, db)

    log_action_service(
        db, user_id,
        "Création fond",
        f"Création fond pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return decision_fond


def get_decision_fond_service(db: Session, decision_id: int) -> Fond:
    decision = get_decision_fond_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision FOND non trouvée")

    return decision


def get_decisions_by_dossier_service(db: Session, dossier_id: int) -> List[Fond]:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    return get_decisions_fond_by_dossier(db, dossier_id)


def get_decisions_by_deliberation_service(db: Session, deliberation_id: int) -> List[Fond]:
    decisions = get_decisions_fond_by_deliberation(db, deliberation_id)
    if not decisions:
        raise HTTPException(
            status_code=404,
            detail="Aucune décision FOND trouvée pour cette délibération"
        )

    return decisions


def get_decisions_par_defaut_service(db: Session) -> List[Fond]:
    return get_decisions_fond_par_defaut(db)


def get_decisions_contradictoires_service(db: Session) -> List[Fond]:
    return get_decisions_fond_contradictoires(db)


def update_decision_fond_service(db: Session, decision_id: int, data: DecisionFondUpdate, user_id: int, copie_decision_fond: Optional[UploadFile] = None) -> Fond:
    decision = get_decision_fond_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision FOND non trouvée")

    dossier = get_dossier_by_id(db, decision.dossier_id)

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    date_decision = data.date_decision_fond or decision.date_decision_fond
    date_notif = data.date_notification or decision.date_notification

    if date_notif and date_decision:
        if date_notif < date_decision:
            raise HTTPException(
                status_code=400,
                detail="La date de notification ne peut pas être antérieure à la date de décision"
            )

    if data.date_notification or data.delai_appel:
        date_notif_final = data.date_notification or decision.date_notification
        delai_final = data.delai_appel or decision.delai_appel
        if date_notif_final:
            data.date_limite_appel = date_notif_final + timedelta(days=delai_final)

    updated_decision = update_decision_fond(db, decision_id, data)

    has_new_file = copie_decision_fond and copie_decision_fond.filename
    if has_new_file:
        process_upload(
            obj=updated_decision,
            files=[copie_decision_fond],
            db=db,
            dossier=dossier,
            file_field="copie_decision_fond",
            contenu_field="observations",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_fond"
        )

    log_action_service(
        db, user_id,
        "Mise à jour fond",
        f"Mise à jour fond pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return updated_decision


def delete_decision_fond_service(db: Session, decision_id: int) -> dict:
    decision = get_decision_fond_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision FOND non trouvée")

    dossier = get_dossier_by_id(db, decision.dossier_id)
    if dossier and dossier.current_stage != ProcessStage.FOND.value:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer une décision FOND si le dossier n'est plus à cette étape"
        )

    success = delete_decision_fond(db, decision_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de la décision FOND"
        )

    return {"message": "Décision FOND supprimée avec succès", "id": decision_id}


def get_pending_alerts_service(db: Session) -> list[Type[Fond]]:
    return get_all_decisions_fond_with_alerts_pending(db)


def mark_alert_as_sent_service(db: Session, decision_id: int) -> Fond:
    decision = get_decision_fond_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision FOND non trouvée")

    update_data = DecisionFondUpdate(alerte_envoyee=True)
    updated_decision = update_decision_fond(db, decision_id, update_data)

    return updated_decision


@celery_app.task()
def check_and_send_fond_alerts():
    db = SessionLocal()
    try:
        decisions = db.query(Fond).filter(
            Fond.alerte_envoyee == False,
            Fond.date_decision_fond.isnot(None)
        ).all()

        today = datetime.utcnow().date()

        for decision in decisions:
            date_alerte = decision.date_decision_fond + timedelta(days=90)
            delta = date_alerte - today
            days_left = delta.days

            if -2 <= days_left <= 0:
                try:
                    email_avocat = decision.dossier.avocat_responsable_user.email if decision.dossier and decision.dossier.avocat_responsable_user else None
                    if not email_avocat:
                        print(f"Aucun email d'avocat trouvé pour la décision fond {decision.id}")
                        continue

                    dossier_info = {
                        "nom_dossier": decision.dossier.nom_dossier if decision.dossier else "Inconnu",
                        "numero_dossier": decision.dossier.numero_dossier if decision.dossier else "Inconnu",
                        "type_alerte": "Récupération de décision au fond",
                        "date_decision": decision.date_decision_fond,
                        "date_alerte": date_alerte
                    }

                    send_delai_alert_email.delay(email=email_avocat, dossier=dossier_info)

                    decision.alerte_envoyee = True
                    db.commit()

                    print(f"Alerte envoyée pour décision fond {decision.id}")

                except Exception as e:
                    print(f"Erreur lors de l'envoi du mail pour décision fond {decision.id} : {str(e)}")
                    db.rollback()
                    continue

    finally:
        db.close()
