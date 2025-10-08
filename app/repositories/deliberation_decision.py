from sqlalchemy.orm import Session, joinedload
from app.models.deliberation_decision import DeliberationDecision
from app.schemas.deliberation_decision import DeliberationDecisionCreate, DeliberationDecisionUpdate


def create_deliberation_decision(db: Session, obj_in: DeliberationDecisionCreate) -> DeliberationDecision:
    db_obj = DeliberationDecision(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_deliberation_decision_by_id(db: Session, id: int):
    deliberation = db.query(DeliberationDecision).options(
        joinedload(DeliberationDecision.decisions_fond),
        joinedload(DeliberationDecision.decisions_add)
    ).filter(DeliberationDecision.id == id).first()
    return deliberation

def get_deliberation_decision_by_dossier(db: Session, dossier_id: int):
    return db.query(DeliberationDecision).filter(DeliberationDecision.dossier_id == dossier_id).all()


def update_deliberation_decision(db: Session, db_obj: DeliberationDecision, obj_in: DeliberationDecisionUpdate):
    for k, v in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj
