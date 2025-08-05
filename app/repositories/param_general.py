from sqlalchemy.orm import Session
from app.models.param_general import ParamGeneral
from sqlalchemy import asc, desc, distinct


def get_all_params(db: Session):
    return db.query(ParamGeneral).order_by(ParamGeneral.nom).all()

def get_all_params_name(db: Session):
    result = db.query(distinct(ParamGeneral.nom)).all()
    return [nom[0] for nom in result]

def get_param_by_nom(db: Session, nom: str) -> ParamGeneral | None:
    return db.query(ParamGeneral).filter(ParamGeneral.nom == nom).first()

def get_param_by_id(db: Session, id: int) -> ParamGeneral | None:
    return db.query(ParamGeneral).filter(ParamGeneral.id == id).first()

def get_param_by_nom_valeur(db :Session, nom: str, valeur: str) -> ParamGeneral | None:
    return db.query(ParamGeneral).filter(ParamGeneral.nom == nom, ParamGeneral.valeur == valeur).first()

def get_params_by_nom_ordered(db: Session, nom: str, order_direction: str = "asc"):
    query = db.query(ParamGeneral).filter(ParamGeneral.nom == nom)
    if order_direction.lower() == "desc":
        query = query.order_by(desc(ParamGeneral.ordre))
    else:
        query = query.order_by(asc(ParamGeneral.ordre))
    return query.all()


def create_param(db: Session, nom: str, valeur: str, unite: str | None = None, ordre: str | None = None) -> ParamGeneral:
    existing_param = get_param_by_nom_valeur(db, nom, valeur)
    if existing_param:
        raise ValueError(f"Le paramètre avec nom '{nom}' et valeur '{valeur}' existe déjà.")

    new_param = ParamGeneral(
        nom=nom,
        valeur=valeur,
        unite=unite,
        ordre=ordre
    )
    db.add(new_param)
    db.commit()
    db.refresh(new_param)
    return new_param


def update_param(db: Session, id: int, nom: str, valeur: str, unite: str | None = None, ordre: str | None = None) -> ParamGeneral | None:
    param = get_param_by_id(db, id)
    if not param:
        return None
    param.nom = nom
    param.valeur = valeur
    param.unite = unite
    param.ordre = ordre
    db.commit()
    db.refresh(param)
    return param


def get_nom_param_general(db: Session, param_id: int) -> str:
    param = db.query(ParamGeneral).filter(ParamGeneral.id == param_id).first()
    return param.nom if param else None

def get_param_by_nom_and_ordre(db: Session, nom: str, ordre: int | str | None):
    if ordre is None:
        return None
    return db.query(ParamGeneral).filter(
        ParamGeneral.nom == nom,
        ParamGeneral.ordre == ordre
    ).first()