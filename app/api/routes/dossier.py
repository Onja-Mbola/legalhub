from fastapi import APIRouter, Depends, Request
from app.core.auth import get_current_avocat_user
from app.models.user import User
from fastapi.templating import Jinja2Templates
from app.services.param_general import get_param_ordered, to_dict_list
from sqlalchemy.orm import Session
from app.db.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers")
def list_dossiers(request: Request, user: User = Depends(get_current_avocat_user)):
    return templates.TemplateResponse("dossiers/liste_dossiers.html", {
        "request": request,
        "user": user,
    })


@router.get("/dossiers/nouveau")
def new_dossier_form(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_avocat_user)
):
    type_affaire = get_param_ordered(db, "type_affaire", "asc")
    urgences = get_param_ordered(db, "urgence", "asc")
    civil_types = get_param_ordered(db, "sous_type_civil", "asc")
    penal_types = get_param_ordered(db, "sous_type_penal", "asc")
    qualite_types = get_param_ordered(db, "qualite_type", "asc")


    return templates.TemplateResponse("dossier/create_dossier.html", {
        "request": request,
        "user": user,
        "type_affaire": to_dict_list(type_affaire),
        "urgences": to_dict_list(urgences),
        "civil_types": to_dict_list(civil_types),
        "penal_types": to_dict_list(penal_types),
        "qualite_types": to_dict_list(qualite_types),
    })
