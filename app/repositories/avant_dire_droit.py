from sqlalchemy.orm import Session
from typing import List, Optional, Type

from app.models.avant_dire_droit import AvantDireDroit
from app.schemas.avant_dire_droit import DecisionADDCreate, DecisionADDUpdate


def create_decision_add(db: Session, obj_in: DecisionADDCreate) -> AvantDireDroit:
    db_obj = AvantDireDroit(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_decision_add_by_id(db: Session, decision_id: int) -> Optional[AvantDireDroit]:
    return db.query(AvantDireDroit).filter(AvantDireDroit.id == decision_id).first()


def get_decisions_add_by_dossier(db: Session, dossier_id: int) -> List[AvantDireDroit]:
    return db.query(AvantDireDroit).filter(
        AvantDireDroit.dossier_id == dossier_id
    ).order_by(AvantDireDroit.date_decision_add.desc()).all()


def get_decisions_add_by_deliberation(db: Session, deliberation_id: int) -> List[AvantDireDroit]:
    return db.query(AvantDireDroit).filter(
        AvantDireDroit.deliberation_decision_id == deliberation_id
    ).all()


def update_decision_add(db: Session, decision_id: int, obj_in: DecisionADDUpdate) -> Optional[AvantDireDroit]:
    db_obj = get_decision_add_by_id(db, decision_id)
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_decision_add(db: Session, decision_id: int) -> bool:
    db_obj = get_decision_add_by_id(db, decision_id)
    if not db_obj:
        return False

    db.delete(db_obj)
    db.commit()
    return True


def get_all_decisions_add_with_alerts_pending(db: Session) -> list[Type[AvantDireDroit]]:
    return db.query(AvantDireDroit).filter(
        AvantDireDroit.alerte_envoyee == False,
        AvantDireDroit.date_limite_conclusions.isnot(None)
    ).all()