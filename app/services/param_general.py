from sqlalchemy.orm import Session
from app.repositories import param_general as repo
from app.models.param_general import ParamGeneral
from app.repositories.param_general import get_nom_param_general, create_param, get_param_by_nom_and_ordre


def list_all_params(db: Session) -> list[ParamGeneral]:
    return repo.get_all_params(db)

def list_all_params_name_service(db: Session) -> list[str]:
    return repo.get_all_params_name(db)
def get_param(db: Session, nom: str) -> ParamGeneral | None:
    return repo.get_param_by_nom(db, nom)

def get_param_id(db: Session, id: int) -> ParamGeneral | None:
    return repo.get_param_by_id(db, id)
def get_param_ordered(db: Session, nom: str, direction: str = "asc") -> list[ParamGeneral]:
    return repo.get_params_by_nom_ordered(db, nom, direction)

def create_param_service(db: Session, nom: str, valeur: str, unite: str | None = None, ordre: str | None = None) -> ParamGeneral:
    existing_param = repo.get_param_by_nom(db, nom)
    if not existing_param:
        raise ValueError(f"Le nom '{nom}' n'existe pas dans la base.")
    ordre_exist = get_param_by_nom_and_ordre_service(db, nom, ordre)
    if ordre_exist:
        raise ValueError(f"L'ordre '{ordre}' existe déjà pour le nom '{nom}'.")
    return create_param(db, nom, valeur, unite, ordre)

def update_param_value(db: Session, id: int, nom: str, valeur: str, unite: str | None = None, ordre: str | None = None) -> ParamGeneral | None:
    existing_param = get_param_id(db, id)
    if not existing_param:
        raise ValueError(f"Le paramètre n'existe pas dans la base.")

    if ordre is not None and ordre != existing_param.ordre:
        ordre_exist = repo.get_param_by_nom_and_ordre(db, nom, ordre)
        if ordre_exist:
            raise ValueError(f"L'ordre '{ordre}' existe déjà pour le nom '{nom}'.")

    return repo.update_param(db, id, nom, valeur, unite, ordre)

def to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
def to_dict_list(obj_list):
    return [to_dict(item) for item in obj_list]

def get_nom_param_general_by_Id(db: Session, param_id: int) -> str:
    return get_nom_param_general(db, param_id)

def get_param_by_nom_and_ordre_service(db: Session, nom: str, ordre: int | str | None):
    return get_param_by_nom_and_ordre(db, nom, ordre)
