from sqlalchemy.orm import Session
from app.models.decision_avant_dire_droit import DecisionAvantDireDroit
from app.schemas.decision_avant_dire_droit import DecisionAvantDireDroitCreate, DecisionAvantDireDroitUpdate


def create_decision_avant_dire_droit(db: Session, obj_in: DecisionAvantDireDroitCreate) -> DecisionAvantDireDroit:
    db_obj = DecisionAvantDireDroit(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_decision_avant_dire_droit_by_id(db: Session, id: int):
    return db.query(DecisionAvantDireDroit).filter(DecisionAvantDireDroit.id == id).first()


def get_decision_avant_dire_droit_by_dossier(db: Session, dossier_id: int):
    return db.query(DecisionAvantDireDroit).filter(DecisionAvantDireDroit.dossier_id == dossier_id).all()


def update_decision_avant_dire_droit(db: Session, db_obj: DecisionAvantDireDroit, obj_in: DecisionAvantDireDroitUpdate):
    for k, v in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj
