from sqlalchemy.orm import Session
from app.models.premiere_audience import PremiereAudience
from app.schemas.premiere_audience import PremiereAudienceCreate, PremiereAudienceUpdate


def create_premiere_audience(db: Session, dossier_id: int, data: PremiereAudienceCreate, pv_audience: str = None):
    db_obj = PremiereAudience(
        dossier_id=dossier_id,
        pv_audience=pv_audience if pv_audience else data.pv_audience,
        decision=data.decision,
        nouvelle_date_audience=data.nouvelle_date_audience,
        nom_judge=data.nom_judge,
        observations_judge=data.observations_judge,
        observations_internes=data.observations_internes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_premiere_audience(db: Session, db_obj: PremiereAudience, data: PremiereAudienceUpdate):
    if data.pv_audience:
        db_obj.pv_audience = data.pv_audience
    if data.decision is not None:
        db_obj.decision = data.decision
    if data.nouvelle_date_audience is not None:
        db_obj.nouvelle_date_audience = data.nouvelle_date_audience
    if data.nom_judge is not None:
        db_obj.nom_judge = data.nom_judge
    if data.observations_judge is not None:
        db_obj.observations_judge = data.observations_judge
    if data.observations_internes is not None:
        db_obj.observations_internes = data.observations_internes

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_premiere_audience(db: Session, audience_id: int):
    return db.query(PremiereAudience).filter(PremiereAudience.id == audience_id).first()


def get_premieres_audiences_by_dossier(db: Session, dossier_id: int):
    return db.query(PremiereAudience).filter(PremiereAudience.dossier_id == dossier_id).all()


def delete_premiere_audience(db: Session, db_obj: PremiereAudience):
    db.delete(db_obj)
    db.commit()
