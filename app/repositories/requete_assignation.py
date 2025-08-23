from sqlalchemy.orm import Session
from app.models.requete_assignation import RequeteAssignation
from app.schemas.requete_assignation import RequeteAssignationCreate, RequeteAssignationUpdate

def create_requete_assignation(db: Session, dossier_id: int, data: RequeteAssignationCreate, assignation_file: str = None, preuve_signification_file: str = None):
    db_obj = RequeteAssignation(
        dossier_id=dossier_id,
        nom_huissier=data.nom_huissier,
        date_signification=data.date_signification,
        date_audience=data.date_audience,
        assignation_file=assignation_file,
        preuve_signification_file=preuve_signification_file
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_requete_assignation(db: Session, db_obj: RequeteAssignation, data: RequeteAssignationUpdate, assignation_file: str = None, preuve_signification_file: str = None):
    if data.nom_huissier is not None:
        db_obj.nom_huissier = data.nom_huissier
    if data.date_signification is not None:
        db_obj.date_signification = data.date_signification
    if data.date_audience is not None:
        db_obj.date_audience = data.date_audience
    if assignation_file:
        db_obj.assignation_file = assignation_file
    if preuve_signification_file:
        db_obj.preuve_signification_file = preuve_signification_file

    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_requete_assignation_by_dossier(db: Session, dossier_id: int) -> RequeteAssignation | None:
    return db.query(RequeteAssignation).filter(RequeteAssignation.dossier_id == dossier_id).first()
