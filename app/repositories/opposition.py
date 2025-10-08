from typing import List, Optional

from sqlalchemy.orm import Session
from app.models.opposition import Opposition
from app.schemas.opposition import OppositionCreate, OppositionUpdate


def create_opposition(db: Session, obj: OppositionCreate):
    db_obj = Opposition(**obj.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_opposition_by_id(db: Session, id: int):
    return db.query(Opposition).filter(Opposition.id == id).first()


def get_oppositions_by_dossier(db: Session, dossier_id: int):
    return db.query(Opposition).filter(Opposition.dossier_id == dossier_id).all()


def get_all_opposition(db: Session):
    return db.query(Opposition).filter(Opposition.alerte_envoyee == False).all()


def update_opposition(db: Session, id: int, obj: OppositionUpdate):
    opposition = get_opposition_by_id(db, id)
    if not opposition:
        return None

    update_data = obj.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(opposition, key, value)

    db.commit()
    db.refresh(opposition)
    return opposition


def get_oppositions_by_jugement(db: Session, jugement_id: int) -> List[Opposition]:
    return db.query(Opposition).filter(Opposition.jugement_id == jugement_id).all()


def get_oppositions_by_decision_fond(db: Session, decision_fond_id: int) -> List[Opposition]:
    return db.query(Opposition).filter(Opposition.decision_fond_id == decision_fond_id).all()


def get_oppositions_non_formulees(db: Session) -> List[Opposition]:
    return db.query(Opposition).filter(
        Opposition.opposition_formulee == False
    ).all()


def delete_opposition(db: Session, opposition_id: int) -> bool:
    opposition = get_opposition_by_id(db, opposition_id)
    if not opposition:
        return False

    db.delete(opposition)
    db.commit()
    return True


def get_oppositions_with_alerts_pending(db: Session) -> List[Opposition]:
    return db.query(Opposition).filter(
        Opposition.alerte_envoyee == False,
        Opposition.opposition_formulee == False
    ).all()
