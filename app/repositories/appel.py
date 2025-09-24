from sqlalchemy.orm import Session
from app.models.appel import Appel
from app.schemas.appel import AppelCreate, AppelUpdate


def create_appel(db: Session, appel_in: AppelCreate) -> Appel:
    appel = Appel(**appel_in.dict())
    db.add(appel)
    db.commit()
    db.refresh(appel)
    return appel


def get_appel_by_id(db: Session, appel_id: int) -> Appel:
    return db.query(Appel).filter(Appel.id == appel_id).first()


def get_appels_by_dossier(db: Session, dossier_id: int):
    return db.query(Appel).filter(Appel.dossier_id == dossier_id).all()


def update_appel(db: Session, appel_id: int, appel_in: AppelUpdate) -> Appel:
    appel = get_appel_by_id(db, appel_id)
    if appel:
        for field, value in appel_in.dict(exclude_unset=True).items():
            setattr(appel, field, value)
        db.commit()
        db.refresh(appel)
    return appel


def delete_appel(db: Session, appel_id: int) -> bool:
    appel = get_appel_by_id(db, appel_id)
    if appel:
        db.delete(appel)
        db.commit()
        return True
    return False
