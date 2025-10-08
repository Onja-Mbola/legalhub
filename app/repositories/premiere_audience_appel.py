from sqlalchemy.orm import Session
from app.models.premiere_audience_appel import PremiereAudienceAppel
from app.schemas.premiere_audience_appel import PremiereAudienceAppelCreate, PremiereAudienceAppelUpdate


def get_premiere_audience_appel_by_dossier(db: Session, dossier_id: int):
    return db.query(PremiereAudienceAppel).filter(
        PremiereAudienceAppel.dossier_id == dossier_id
    ).first()


def get_premiere_audience_appel_by_enrolement(db: Session, enrolement_appel_id: int):
    return db.query(PremiereAudienceAppel).filter(
        PremiereAudienceAppel.enrolement_appel_id == enrolement_appel_id
    ).first()


def create_premiere_audience_appel(
    db: Session,
    dossier_id: int,
    premiere_audience_appel_in: PremiereAudienceAppelCreate
) -> PremiereAudienceAppel:
    premiere_audience_appel = PremiereAudienceAppel(
        dossier_id=dossier_id,
        **premiere_audience_appel_in.dict()
    )
    db.add(premiere_audience_appel)
    db.commit()
    db.refresh(premiere_audience_appel)
    return premiere_audience_appel


def update_premiere_audience_appel(
    db: Session,
    premiere_audience_appel: PremiereAudienceAppel,
    premiere_audience_appel_in: PremiereAudienceAppelUpdate
) -> PremiereAudienceAppel:
    for field, value in premiere_audience_appel_in.dict(exclude_unset=True).items():
        setattr(premiere_audience_appel, field, value)
    db.commit()
    db.refresh(premiere_audience_appel)
    return premiere_audience_appel


def get_premiere_audience_appel_by_id(db: Session, audience_id: int):
    return db.query(PremiereAudienceAppel).filter(
        PremiereAudienceAppel.id == audience_id
    ).first()