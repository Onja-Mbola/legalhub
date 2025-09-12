from sqlalchemy.orm import Session
from app.models.retour_audience import RetourAudience
from app.schemas.retour_audience import RetourAudienceCreate, RetourAudienceUpdate


def create_retour_audience(db: Session, retour_data: RetourAudienceCreate) -> RetourAudience:
    retour = RetourAudience(**retour_data.dict())
    db.add(retour)
    db.commit()
    db.refresh(retour)
    return retour


def get_retour_audience(db: Session, retour_id: int) -> RetourAudience:
    return db.query(RetourAudience).filter(RetourAudience.id == retour_id).first()


def get_retours_by_dossier(db: Session, dossier_id: int):
    return db.query(RetourAudience).filter(RetourAudience.dossier_id == dossier_id).all()


def update_retour_audience(db: Session, retour_id: int, update_data: RetourAudienceUpdate) -> RetourAudience:
    retour = get_retour_audience(db, retour_id)
    if not retour:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(retour, key, value)
    db.commit()
    db.refresh(retour)
    return retour
