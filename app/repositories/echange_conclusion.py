from sqlalchemy.orm import Session
from app.models.echange_conclusion import EchangeConclusion
from app.schemas.echange_conclusion import EchangeConclusionCreate, EchangeConclusionUpdate


def create_echange_conclusion(db: Session, obj_in: EchangeConclusionCreate) -> EchangeConclusion:
    db_obj = EchangeConclusion(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_echange_conclusion_by_id(db: Session, id: int):
    return db.query(EchangeConclusion).filter(EchangeConclusion.id == id).first()


def get_echange_conclusion_by_dossier(db: Session, dossier_id: int):
    return db.query(EchangeConclusion).filter(EchangeConclusion.dossier_id == dossier_id).all()

def get_echanges_by_retour(db: Session, retour_audience_id: int):
    return db.query(EchangeConclusion).filter(EchangeConclusion.retour_audience_id == retour_audience_id).all()


def update_echange_conclusion(db: Session, db_obj: EchangeConclusion, obj_in: EchangeConclusionUpdate):
    for k, v in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj
