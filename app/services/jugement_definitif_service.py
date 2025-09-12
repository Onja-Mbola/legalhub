from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.repositories.dossier import get_dossier_by_id
from app.repositories.jugement_definitif import get_jugements_definitifs_by_dossier, update_jugement_definitif, \
    get_jugement_definitif, create_jugement_definitif
from app.schemas.jugement_definitif import (
    JugementDefinitifCreate,
    JugementDefinitifUpdate,
    JugementDefinitifOut,
)
from app.services.workflow_guard import WorkflowGuard


def create_jugement_definitif_service(
        db: Session,
        dossier_id: int,
        deliberation_id: int,
        date_jugement: datetime,
        texte_jugement: str | None = None,
        jugement_file: list[str] | None = None,
        observations: str | None = None,
        date_notification: datetime | None = None,
) -> dict:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT.value:
        raise HTTPException(
            status_code=400,
            detail="Vous devez d'abord passer par la Délibération avant d'enregistrer un Jugement Définitif."
        )

    obj_in = JugementDefinitifCreate(
        dossier_id=dossier_id,
        deliberation_id=deliberation_id,
        date_jugement=date_jugement,
        texte_jugement=texte_jugement,
        jugement_file=jugement_file,
        observations=observations,
    )

    jugement = create_jugement_definitif(db, obj_in)

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_DEFINITIF, db)

    appel_possible_jusqua = None
    if date_notification:
        appel_possible_jusqua = date_notification + timedelta(days=30)

    return {
        "jugement": JugementDefinitifOut.from_orm(jugement),
        "date_notification": date_notification,
        "appel_possible_jusqua": appel_possible_jusqua,
    }


def get_jugement_definitif_service(db: Session, jugement_id: int) -> JugementDefinitifOut:
    jugement = get_jugement_definitif(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement Définitif non trouvé")
    return JugementDefinitifOut.from_orm(jugement)


def update_jugement_definitif_service(
        db: Session,
        jugement_id: int,
        update_data: JugementDefinitifUpdate
) -> JugementDefinitifOut:
    jugement = update_jugement_definitif(db, jugement_id, update_data)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement Définitif non trouvé pour mise à jour")
    return JugementDefinitifOut.from_orm(jugement)


def get_jugements_definitifs_by_dossier_service(db: Session, dossier_id: int):
    return get_jugements_definitifs_by_dossier(db, dossier_id)
