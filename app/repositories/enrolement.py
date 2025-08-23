from sqlalchemy.orm import Session
from app.models.enrolement import Enrolement
from app.schemas.enrolement import EnrolementCreate, EnrolementUpdate


def get_enrolement_by_dossier(db: Session, dossier_id: int) -> Enrolement | None:
    return db.query(Enrolement).filter(Enrolement.dossier_id == dossier_id).first()


def create_enrolement(db: Session, dossier_id: int, enrolement_in: EnrolementCreate) -> Enrolement:
    enrolement = Enrolement(dossier_id=dossier_id, **enrolement_in.dict())
    db.add(enrolement)
    db.commit()
    db.refresh(enrolement)
    return enrolement


def update_enrolement(db: Session, enrolement: Enrolement, enrolement_in: EnrolementUpdate) -> Enrolement:
    for field, value in enrolement_in.dict(exclude_unset=True).items():
        setattr(enrolement, field, value)
    db.commit()
    db.refresh(enrolement)
    return enrolement


def get_enrolement_by_numero_role(db: Session, numero_role: int):
    return db.query(Enrolement).filter(Enrolement.numero_role == numero_role).first()
