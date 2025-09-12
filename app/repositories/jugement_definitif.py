from sqlalchemy.orm import Session
from app.models.jugement_definitif import JugementDefinitif
from app.schemas.jugement_definitif import JugementDefinitifCreate, JugementDefinitifUpdate


def create_jugement_definitif(db: Session, obj_in: JugementDefinitifCreate):
    db_obj = JugementDefinitif(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_jugement_definitif(db: Session, id: int):
    return db.query(JugementDefinitif).filter(JugementDefinitif.id == id).first()


def get_jugements_definitifs_by_dossier(db: Session, dossier_id: int):
    return db.query(JugementDefinitif).filter(JugementDefinitif.dossier_id == dossier_id).all()


def update_jugement_definitif(db: Session, db_obj: JugementDefinitif, obj_in: JugementDefinitifUpdate):
    for field, value in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
