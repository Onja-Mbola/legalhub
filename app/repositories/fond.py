from typing import List, Optional, Type

from sqlalchemy.orm import Session

from app.models.fond import Fond
from app.schemas.fond import DecisionFondCreate, DecisionFondUpdate


def create_decision_fond(db: Session, obj_in: DecisionFondCreate) -> Fond:
    db_obj = Fond(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_decision_fond_by_id(db: Session, decision_id: int) -> Optional[Fond]:
    return db.query(Fond).filter(Fond.id == decision_id).first()


def get_decisions_fond_by_dossier(db: Session, dossier_id: int) -> List[Fond]:
    return db.query(Fond).filter(
        Fond.dossier_id == dossier_id
    ).order_by(Fond.date_decision_fond.desc()).all()


def get_decisions_fond_by_deliberation(db: Session, deliberation_id: int) -> List[Fond]:
    return db.query(Fond).filter(
        Fond.deliberation_decision_id == deliberation_id
    ).all()


def get_decisions_fond_par_defaut(db: Session) -> List[Fond]:
    return db.query(Fond).filter(
        Fond.type_decision_fond == "par_defaut"
    ).all()


def get_decisions_fond_contradictoires(db: Session) -> List[Fond]:
    return db.query(Fond).filter(
        Fond.type_decision_fond == "contradictoire"
    ).all()


def update_decision_fond(db: Session, decision_id: int, obj_in: DecisionFondUpdate) -> Optional[Fond]:
    db_obj = get_decision_fond_by_id(db, decision_id)
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_decision_fond(db: Session, decision_id: int) -> bool:
    db_obj = get_decision_fond_by_id(db, decision_id)
    if not db_obj:
        return False

    db.delete(db_obj)
    db.commit()
    return True


def get_all_decisions_fond_with_alerts_pending(db: Session) -> list[Type[Fond]]:
    return db.query(Fond).filter(
        Fond.alerte_envoyee == False,
        Fond.date_limite_appel.isnot(None)
    ).all()
