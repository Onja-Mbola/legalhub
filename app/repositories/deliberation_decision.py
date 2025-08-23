from sqlalchemy.orm import Session
from app.models.deliberation_decision import Deliberation_Decision
from app.schemas.deliberation_decision import DeliberationDecisionCreate, DeliberationDecisionUpdate


def create_deliberation_decision(db: Session, obj_in: DeliberationDecisionCreate) -> Deliberation_Decision:
    db_obj = Deliberation_Decision(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_deliberation_decision_by_id(db: Session, id: int):
    return db.query(Deliberation_Decision).filter(Deliberation_Decision.id == id).first()


def get_deliberation_decision_by_dossier(db: Session, dossier_id: int):
    return db.query(Deliberation_Decision).filter(Deliberation_Decision.dossier_id == dossier_id).all()


def update_deliberation_decision(db: Session, db_obj: Deliberation_Decision, obj_in: DeliberationDecisionUpdate):
    for k, v in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj
