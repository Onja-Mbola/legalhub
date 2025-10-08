from typing import List, Optional, Type
from sqlalchemy.orm import Session
from app.models.cassation import Cassation
from app.schemas.cassation import CassationCreate, CassationUpdate


def create_cassation(db: Session, obj_in: CassationCreate) -> Cassation:
    db_obj = Cassation(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_cassation_by_id(db: Session, cassation_id: int) -> Optional[Cassation]:
    return db.query(Cassation).filter(Cassation.id == cassation_id).first()


def get_cassation_by_decision_fond(db: Session, decision_fond_id: int) -> Optional[Cassation]:
    return db.query(Cassation).filter(
        Cassation.decision_fond_id == decision_fond_id
    ).first()


def get_cassations_by_dossier(db: Session, dossier_id: int) -> List[Cassation]:
    return db.query(Cassation).filter(
        Cassation.dossier_id == dossier_id
    ).order_by(Cassation.date_notification_decision.desc()).all()


def get_all_cassations(db: Session) -> list[Type[Cassation]]:
    return db.query(Cassation).order_by(Cassation.date_notification_decision.desc()).all()


def get_cassations_by_statut(db: Session, statut: str) -> List[Cassation]:
    return db.query(Cassation).filter(
        Cassation.statut == statut
    ).all()


def update_cassation(db: Session, cassation_id: int, obj_in: CassationUpdate) -> Optional[Cassation]:
    db_obj = get_cassation_by_id(db, cassation_id)
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_cassation(db: Session, cassation_id: int) -> bool:
    db_obj = get_cassation_by_id(db, cassation_id)
    if not db_obj:
        return False

    db.delete(db_obj)
    db.commit()
    return True


def get_cassations_with_pending_alerts(db: Session) -> List[Cassation]:
    return db.query(Cassation).filter(
        (Cassation.alerte_requete_envoyee == False) |
        (Cassation.alerte_memoire_ampliatif_envoyee == False)
    ).all()
