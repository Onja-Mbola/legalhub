from datetime import timedelta, datetime, date
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.core.workflow_enums import ProcessStage
from app.db.session import SessionLocal
from app.models.opposition import Opposition
from app.repositories import opposition as opposition_repo
from app.repositories.dossier import get_dossier_by_id
from app.repositories.fond import get_decision_fond_by_id
from app.repositories.opposition import get_all_opposition
from app.schemas.opposition import OppositionCreate, OppositionUpdate, OppositionOut
from app.services.email import send_opposition_email_programmer
from app.services.upload_processor import process_upload
from app.services.workflow_guard import WorkflowGuard


def create_opposition_appel_auto(db: Session, decision_fond_id: int, date_notification: date) -> Opposition:
    decision = get_decision_fond_by_id(db, decision_fond_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision FOND non trouvée")

    if date_notification < decision.date_decision_fond:
        raise HTTPException(
            status_code=400,
            detail="La date de notification ne peut pas être antérieure à la date de décision"
        )

    opposition_possible_jusqua = date_notification + timedelta(days=15)

    opposition = Opposition(
        dossier_id=decision.dossier_id,
        decision_fond_id=decision_fond_id,
        jugement_id=None,
        date_notification=date_notification,
        opposition_possible_jusqua=opposition_possible_jusqua,
        opposition_formulee=False
    )

    db.add(opposition)
    db.commit()
    db.refresh(opposition)

    return opposition


def update_opposition_appel_service(
        db: Session,
        opposition_id: int,
        date_opposition: date,
        acte_opposition_file: Optional[UploadFile] = None,  # Accepter le UploadFile
        motifs_opposition: Optional[str] = None
) -> Opposition:
    opposition = opposition_repo.get_opposition_by_id(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée")

    today = datetime.now().date()
    if today > opposition.opposition_possible_jusqua:
        raise HTTPException(
            status_code=400,
            detail=f"Le délai d'opposition de 15 jours est dépassé. Date limite: {opposition.opposition_possible_jusqua}"
        )

    if date_opposition < opposition.date_notification:
        raise HTTPException(
            status_code=400,
            detail="La date d'opposition ne peut pas être antérieure à la date de notification"
        )

    if date_opposition > opposition.opposition_possible_jusqua:
        raise HTTPException(
            status_code=400,
            detail=f"La date d'opposition ne peut pas dépasser la date limite ({opposition.opposition_possible_jusqua})"
        )

    update_data = OppositionUpdate(
        opposition_formulee=True,
        date_opposition=date_opposition,
        # acte_opposition=None
        motifs_opposition=motifs_opposition
    )

    updated_opposition = opposition_repo.update_opposition(db, opposition_id, update_data)

    if not updated_opposition:
        raise HTTPException(status_code=400, detail="Échec de la mise à jour de l'opposition")

    dossier = updated_opposition.dossier
    if acte_opposition_file and acte_opposition_file.filename:
        files = [acte_opposition_file]
        process_upload(
            obj=updated_opposition,
            files=files,
            db=db,
            dossier=dossier,
            file_field="acte_opposition",
            contenu_field="motifs_opposition",
            ocr_all_files=False,
            run_ml=True,
            subfolder="opposition_Fond"
        )
    else:
        process_upload(
            obj=updated_opposition,
            files=[],
            db=db,
            dossier=dossier,
            file_field="acte_opposition",
            contenu_field="motifs_opposition",
            run_ml=True,
            subfolder="opposition_Fond"
        )
        pass

    db.refresh(updated_opposition)
    return updated_opposition


def create_opposition_service(
        db: Session,
        dossier_id: int,
        jugement_id: int,
        date_notification: datetime,
) -> Opposition:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.PAR_DEFAUT.value:
        raise HTTPException(
            status_code=400,
            detail="Vous devez d'abord passer par le Choix du Jugement avant de passer à l'Opposition."
        )

    opposition_possible_jusqua = date_notification + timedelta(days=15)

    obj = OppositionCreate(
        dossier_id=dossier_id,
        jugement_id=jugement_id,
        date_notification=date_notification,
        opposition_possible_jusqua=opposition_possible_jusqua,
    )

    reponse = opposition_repo.create_opposition(db, obj)
    WorkflowGuard.advance(dossier, ProcessStage.OPPOSITION, db)
    return reponse


def get_opposition_service(db: Session, opposition_id: int) -> OppositionOut:
    opposition = opposition_repo.get_opposition_by_id(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée")
    return opposition


def get_oppositions_by_dossier_service(db: Session, dossier_id: int):
    return opposition_repo.get_oppositions_by_dossier(db, dossier_id)


def update_opposition_service(
        db: Session,
        opposition_id: int,
        update_data: OppositionUpdate
) -> Opposition:
    opposition = opposition_repo.get_opposition_by_id(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée")

    today = datetime.now().date()
    if today > opposition.opposition_possible_jusqua:
        raise HTTPException(
            status_code=400,
            detail=f"Le délai d'opposition de 15 jours est dépassé. Date limite: {opposition.opposition_possible_jusqua}"
        )

    if update_data.date_notification is not None:
        update_data.opposition_possible_jusqua = update_data.date_notification + timedelta(days=15)

        if update_data.date_opposition and update_data.date_opposition < update_data.date_notification:
            raise HTTPException(
                status_code=400,
                detail="La date d'opposition ne peut pas être antérieure à la date de notification"
            )

    if update_data.date_opposition is not None:
        date_notif = update_data.date_notification or opposition.date_notification
        date_limite = update_data.opposition_possible_jusqua or opposition.opposition_possible_jusqua

        if update_data.date_opposition < date_notif:
            raise HTTPException(
                status_code=400,
                detail="La date d'opposition ne peut pas être antérieure à la date de notification"
            )

        if update_data.date_opposition > date_limite:
            raise HTTPException(
                status_code=400,
                detail=f"La date d'opposition ne peut pas dépasser la date limite ({date_limite})"
            )

    updated_opposition = opposition_repo.update_opposition(db, opposition_id, update_data)
    if not updated_opposition:
        raise HTTPException(status_code=400, detail="Échec de la mise à jour de l'opposition")

    return updated_opposition


def check_opposition_exists_for_dossier(db: Session, dossier_id: int) -> Optional[Opposition]:
    oppositions = opposition_repo.get_oppositions_by_dossier(db, dossier_id)

    for opp in oppositions:
        if opp.decision_fond_id is not None and not opp.opposition_formulee:
            return opp

    return None


@celery_app.task()
def check_and_send_opposition_appel_alerts():
    db = SessionLocal()
    try:
        oppositions = db.query(Opposition).filter(
            Opposition.alerte_envoyee == False,
            Opposition.opposition_formulee == False,
            Opposition.decision_fond_id.isnot(None)
        ).all()

        today = datetime.utcnow().date()

        for opposition in oppositions:
            days_left = (opposition.opposition_possible_jusqua - today).days

            if 0 <= days_left <= 5:
                try:
                    email_avocat = opposition.dossier.avocat_responsable_user.email if opposition.dossier.avocat_responsable_user else None

                    if not email_avocat:
                        print(f"Aucun email d'avocat trouvé pour l'opposition {opposition.id}")
                        continue

                    dossier_info = {
                        "nom_dossier": opposition.dossier.nom_dossier,
                        "numero_dossier": opposition.dossier.numero_dossier,
                        "type_alerte": "Opposition possible (décision par défaut)",
                        "date_limite": opposition.opposition_possible_jusqua,
                        "days_left": days_left
                    }

                    send_opposition_email_programmer.delay(email=email_avocat, dossier=dossier_info)

                    opposition.alerte_envoyee = True
                    db.commit()

                except Exception as e:
                    print(f"Erreur lors de l'envoi du mail pour opposition appel {opposition.id} : {str(e)}")
                    db.rollback()
                    continue

    finally:
        db.close()


@celery_app.task()
def check_and_send_alerts():
    db = SessionLocal()
    try:
        oppositions = get_all_opposition(db)
        today = datetime.utcnow().date()

        for opposition in oppositions:
            if not opposition.alerte_envoyee and opposition.jugement_id is not None:
                if opposition.opposition_possible_jusqua:
                    days_left = (opposition.opposition_possible_jusqua - today).days

                    if days_left <= 5 and days_left >= 0:
                        try:
                            email_avocat = opposition.dossier.avocat_responsable_user.email if opposition.dossier.avocat_responsable_user else None

                            if not email_avocat:
                                print(f"Aucun email trouvé pour l'opposition {opposition.id}")
                                continue

                            dossier_info = {
                                "nom_dossier": opposition.dossier.nom_dossier,
                                "numero_dossier": opposition.dossier.numero_dossier,
                                "date_notification": opposition.date_notification,
                                "opposition_possible_jusqua": opposition.opposition_possible_jusqua,
                                "days_left": days_left
                            }

                            send_opposition_email_programmer.delay(email=email_avocat, dossier=dossier_info)

                            opposition.alerte_envoyee = True
                            db.commit()

                        except Exception as e:
                            print(f"Erreur lors de l'envoi du mail pour l'opposition {opposition.id} : {str(e)}")
                            db.rollback()
                            continue
    finally:
        db.close()


@celery_app.task()
def check_and_send_alerts_1():
    db = SessionLocal()
    try:
        oppositions = get_all_opposition(db)
        today = datetime.utcnow().date()

        for opposition in oppositions:
            if not opposition.alerte_envoyee:
                try:
                    email_avocat = opposition.dossier.avocat_responsable_user.email
                    days_left = (opposition.opposition_possible_jusqua - today).days
                    dossier_info = {
                        "nom_dossier": opposition.dossier.nom_dossier,
                        "numero_dossier": opposition.dossier.numero_dossier,
                        "date_notification": opposition.date_notification,
                        "opposition_possible_jusqua": opposition.opposition_possible_jusqua,
                        "days_left": days_left
                    }

                    send_opposition_email_programmer.delay(
                        email=email_avocat,
                        dossier=dossier_info
                    )

                    opposition.alerte_envoyee = True
                    db.commit()

                except Exception as e:
                    print(f"Erreur lors de l'envoi du mail pour l'opposition {opposition.id} : {str(e)}")
                    db.rollback()
                    continue

    finally:
        db.close()
