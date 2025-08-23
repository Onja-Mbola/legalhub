from sqlalchemy.orm import Session
from app.models.decision_definitive import DecisionDefinitive
from app.schemas.decision_definitive import DecisionDefinitiveCreate, DecisionDefinitiveUpdate


def create_decision_definitive(db: Session, obj_in: DecisionDefinitiveCreate) -> DecisionDefinitive:
    db_obj = DecisionDefinitive(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_decision_definitive_by_id(db: Session, id: int):
    return db.query(DecisionDefinitive).filter(DecisionDefinitive.id == id).first()


def get_decision_definitive_by_dossier(db: Session, dossier_id: int):
    return db.query(DecisionDefinitive).filter(DecisionDefinitive.dossier_id == dossier_id).first()


def update_decision_definitive(db: Session, db_obj: DecisionDefinitive, obj_in: DecisionDefinitiveUpdate):
    for k, v in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj
