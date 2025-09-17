from datetime import datetime, timedelta

from sqlalchemy import join, or_
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.dossier import Dossier
from app.models.jugement import Jugement
from app.schemas.jugement import JugementCreate, JugementUpdate

def create_jugement(db: Session, jugement: JugementCreate):
    db_jugement = Jugement(**jugement.dict())
    db.add(db_jugement)
    db.commit()
    db.refresh(db_jugement)
    return db_jugement

def create_jugement_defavorable(db: Session, jugement: JugementCreate):
    db_jugement = Jugement(**jugement.dict())
    db.add(db_jugement)
    db.commit()
    db.refresh(db_jugement)
    return db_jugement

def get_jugement_by_id(db: Session, jugement_id: int):
    return db.query(Jugement).filter(Jugement.id == jugement_id).first()

def get_jugements_by_dossier(db: Session, dossier_id: int):
    return db.query(Jugement).filter(Jugement.dossier_id == dossier_id).all()

def update_jugement(db: Session, jugement_id: int, jugement: JugementUpdate):
    db_jugement = get_jugement_by_id(db, jugement_id)
    if not db_jugement:
        return None
    for key, value in jugement.dict(exclude_unset=True).items():
        setattr(db_jugement, key, value)
    db.commit()
    db.refresh(db_jugement)
    return db_jugement

def delete_jugement(db: Session, jugement_id: int):
    db_jugement = get_jugement_by_id(db, jugement_id)
    if db_jugement:
        db.delete(db_jugement)
        db.commit()
    return db_jugement


def get_jugement_sans_grosse(db: Session, jours_retard: int = 30):
    limite = datetime.utcnow().date() - timedelta(days=jours_retard)

    return (
        db.query(Jugement)
        .join(Dossier)
        .filter(
            Dossier.current_stage == ProcessStage.NOTIFICATION_CLIENT.value,
            Jugement.date_jugement <= limite,
            Jugement.scans_grosse.is_(None),
        )
        .all()
    )