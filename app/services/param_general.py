from sqlalchemy.orm import Session
from app.repositories import param_general as repo
from app.models.param_general import ParamGeneral
from app.repositories.param_general import get_nom_param_general


def list_all_params(db: Session) -> list[ParamGeneral]:
    return repo.get_all_params(db)
def get_param(db: Session, nom: str) -> ParamGeneral | None:
    return repo.get_param_by_nom(db, nom)
def get_param_ordered(db: Session, nom: str, direction: str = "asc") -> list[ParamGeneral]:
    return repo.get_params_by_nom_ordered(db, nom, direction)
def update_param_value(db: Session, nom: str, valeur: str, unite: str | None = None) -> ParamGeneral | None:
    existing_param = repo.get_param_by_nom(db, nom)
    if not existing_param:
        raise ValueError(f"Le nom '{nom}' n'existe pas dans la base.")
    return repo.update_param(db, nom, valeur, unite)
def to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
def to_dict_list(obj_list):
    return [to_dict(item) for item in obj_list]

def get_nom_param_general_by_Id(db: Session, param_id: int) -> str:
    return get_nom_param_general(db, param_id)
