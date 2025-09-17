from sqlalchemy.orm import Session
from app.models.opposition import Opposition
from app.schemas.opposition import OppositionCreate, OppositionUpdate


def create_opposition(db: Session, obj: OppositionCreate):
    db_obj = Opposition(**obj.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_opposition_by_id(db: Session, id: int):
    return db.query(Opposition).filter(Opposition.id == id).first()


def get_oppositions_by_dossier(db: Session, dossier_id: int):
    return db.query(Opposition).filter(Opposition.dossier_id == dossier_id).all()

def get_all_opposition(db :Session):
    return db.query(Opposition).filter(Opposition.alerte_envoyee == False).all()



def update_opposition(db: Session, id: int, obj: OppositionUpdate):
    opposition = get_opposition_by_id(db, id)
    if not opposition:
        return None

    update_data = obj.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(opposition, key, value)

    db.commit()
    db.refresh(opposition)
    return opposition
