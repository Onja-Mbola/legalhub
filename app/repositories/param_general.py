from sqlalchemy.orm import Session
from app.models.param_general import ParamGeneral
from sqlalchemy import asc, desc


def get_all_params(db: Session):
    return db.query(ParamGeneral).all()

def get_param_by_nom(db: Session, nom: str) -> ParamGeneral | None:
    return db.query(ParamGeneral).filter(ParamGeneral.nom == nom).first()

def get_params_by_nom_ordered(db: Session, nom: str, order_direction: str = "asc"):
    query = db.query(ParamGeneral).filter(ParamGeneral.nom == nom)
    if order_direction.lower() == "desc":
        query = query.order_by(desc(ParamGeneral.ordre))
    else:
        query = query.order_by(asc(ParamGeneral.ordre))
    return query.all()
def update_param(db: Session, nom: str, valeur: str, unite: str | None = None) -> ParamGeneral | None:
    param = get_param_by_nom(db, nom)
    if not param:
        return None
    param.valeur = valeur
    param.unite = unite
    db.commit()
    db.refresh(param)
    return param
