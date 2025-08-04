import json
import os
from typing import List

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from starlette.responses import RedirectResponse, HTMLResponse, FileResponse

from app.core.auth import get_current_avocat_user
from app.models.user import User
from fastapi.templating import Jinja2Templates

from app.schemas.dossier import DossierOut, DossierCreate
from app.services.dossier import create_new_dossier_with_files, get_dossiers_by_avocat_service, \
    get_dossier_by_id_service, update_dossier_with_files_service
from app.services.param_general import get_param_ordered, to_dict_list
from sqlalchemy.orm import Session
from app.db.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers")
def list_dossiers(request: Request,db: Session = Depends(get_db), user: User = Depends(get_current_avocat_user)):
    dossiers = get_dossiers_by_avocat_service(db, user.id)
    return templates.TemplateResponse("dossier/liste_dossier.html", {
        "request": request,
        "user": user,
        "dossiers": dossiers
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
    role_types = get_param_ordered(db, "role_type", "asc")


    return templates.TemplateResponse("dossier/create_dossier.html", {
        "request": request,
        "user": user,
        "type_affaire": to_dict_list(type_affaire),
        "urgences": to_dict_list(urgences),
        "civil_types": to_dict_list(civil_types),
        "penal_types": to_dict_list(penal_types),
        "qualite_types": to_dict_list(qualite_types),
        "role_types": to_dict_list(role_types),
    })


@router.post("/dossiers/nouveau")
async def create_dossier_endpoint(
    dossier_data: str = Form(...),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_avocat_user)
):
    avocat_nom = user.nom
    dossier_in = DossierCreate(**json.loads(dossier_data))

    try:
        create_new_dossier_with_files(db, dossier_in, avocat_nom, files)
        return {"redirect_url": "/dossiers?success=1"}

    except SQLAlchemyError:
        db.rollback()
        return {"redirect_url": "/dossiers/nouveau?error=1"}



@router.get("/dossiers/{dossier_id}", response_class=HTMLResponse)
async def voir_dossier(dossier_id: int, request: Request, db: Session = Depends(get_db), user = Depends(get_current_avocat_user)):
    dossier = get_dossier_by_id_service(db, dossier_id)
    return templates.TemplateResponse("dossier/detail_dossier.html", {"request": request, "dossier": dossier, "user": user})


@router.get("/dossiers/{dossier_id}/modifier", response_class=HTMLResponse)
async def edit_dossier(dossier_id: int, request: Request, db: Session = Depends(get_db), user = Depends(get_current_avocat_user)):
    dossier = get_dossier_by_id_service(db, dossier_id)
    return templates.TemplateResponse("dossier/modifier_dossier.html", {"request": request, "dossier": dossier, "user": user})


@router.post("/dossiers/{dossier_id}/modifier")
async def update_dossier(dossier_id: int, nom_dossier: str = Form(...), commentaire: str = Form(None), pieces_jointes: List[UploadFile] = File(None), db: Session = Depends(get_db),user = Depends(get_current_avocat_user)):
    update_dossier_with_files_service(db, dossier_id,user.nom, nom_dossier, commentaire, pieces_jointes)
    return RedirectResponse(url=f"/dossiers/{dossier_id}", status_code=303)


@router.get("/documents/{filepath:path}", name="documents")
async def documents(filepath: str):
    base_dir = os.path.abspath("app/documents")
    full_path = os.path.join(base_dir, filepath)

    if not os.path.commonpath([base_dir, os.path.abspath(full_path)]) == base_dir:
        return {"error": "Accès interdit"}

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path, filename=os.path.basename(full_path))
    return {"error": "Fichier non trouvé"}
