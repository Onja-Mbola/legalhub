from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories import appel as appel_repo
from app.schemas.appel import AppelCreate, AppelUpdate
from app.services.dossier import get_dossier_by_id_service
from app.services.action_log import log_action_service
from app.services.jugement_service import get_jugement_by_dossier_service
from app.services.workflow_guard import WorkflowGuard
from app.core.workflow_enums import ProcessStage


def create_appel_service(db: Session, dossier_id: int, user_id: int, appel_in: AppelCreate):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.JUGEMENT_CONTRADICTOIRE.value:
        raise HTTPException(
            status_code=400,
            detail="Un appel ne peut être créé qu'après un jugement contradictoire."
        )

    jugements = get_jugement_by_dossier_service(db, dossier.id)
    if not jugements:
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer un appel : jugement non notifié."
        )

    jugement = jugements[0]
    if not jugement.date_notification:
        raise HTTPException(
            status_code=400,
            detail="Impossible de créer un appel : jugement non notifié."
        )


    today = datetime.utcnow().date()
    date_notif = jugement.date_notification

    if not jugement.delai_appel:
        raise HTTPException(
            status_code=400,
            detail="Le délai d'appel n'est pas défini pour ce jugement."
        )

    date_limite = date_notif + timedelta(days=jugement.delai_appel)
    days_left = (date_limite - today).days

    if today > date_limite:
        raise HTTPException(
            status_code=400,
            detail=f"Le délai d'appel a expiré le {date_limite.strftime('%d/%m/%Y')}."
        )

    try:
        appel = appel_repo.create_appel(db, appel_in)

        WorkflowGuard.advance(dossier, ProcessStage.APPEL, db)

        log_action_service(
            db,
            user_id,
            "Création appel",
            f"Appel créé pour le dossier {dossier.numero_dossier}. "
            f"Délai restant : {days_left} jours (limite {date_limite.strftime('%d/%m/%Y')}).",
            dossier.id
        )

        return appel
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de l'appel : {str(e)}"
        )


def get_appel_service(db: Session, appel_id: int):
    appel = appel_repo.get_appel_by_id(db, appel_id)
    if not appel:
        raise HTTPException(status_code=404, detail="Appel non trouvé")
    return appel


def get_appels_for_dossier_service(db: Session, dossier_id: int):
    appels = appel_repo.get_appels_by_dossier(db, dossier_id)
    if not appels:
        raise HTTPException(status_code=404, detail="Appel non trouvé pour ce dossier")
    return appels


def update_appel_service(db: Session, appel_id: int, user_id: int, appel_in: AppelUpdate):
    appel = appel_repo.get_appel_by_id(db, appel_id)
    if not appel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appel non trouvé")

    try:
        updated_appel = appel_repo.update_appel(db, appel_id, appel_in)

        log_action_service(
            db,
            user_id,
            "Mise à jour appel",
            f"Mise à jour de l'appel pour le dossier {appel.dossier.numero_dossier}",
            appel.dossier.id
        )

        return updated_appel
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de l'appel: {str(e)}"
        )


def delete_appel_service(db: Session, appel_id: int, user_id: int):
    appel = appel_repo.get_appel_by_id(db, appel_id)
    if not appel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appel non trouvé")

    try:
        dossier_id = appel.dossier.id
        dossier = get_dossier_by_id_service(db, dossier_id)
        dossier_numero = appel.dossier.numero_dossier
        success = appel_repo.delete_appel(db, appel_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de supprimer l'appel")

        log_action_service(
            db,
            user_id,
            "Suppression appel",
            f"Suppression de l'appel pour le dossier {dossier_numero}",
            dossier_id
        )
        WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_CONTRADICTOIRE, db)

        return {"msg": "Appel supprimé avec succès"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de l'appel: {str(e)}"
        )
