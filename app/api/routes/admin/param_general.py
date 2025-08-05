import os
from typing import List

from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException

from app.core.auth import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.param_general import ParamGeneral
from app.services import param_general as service

router = APIRouter(prefix="/admin/params", tags=["Paramètres généraux"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def list_params_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    params = service.list_all_params(db)
    return templates.TemplateResponse("admin/params/list_params.html", {
        "request": request,
        "params": params,
        "user" : current_user
    })


@router.get("/create", response_class=HTMLResponse)
def create_param_form(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    noms_existants = service.list_all_params_name_service(db)
    return templates.TemplateResponse("admin/params/create_param.html", {
        "request": request,
        "user": current_user,
        "noms_existants": noms_existants
    })


@router.post("/create")
def create_param_action(
    request: Request,
    nom: str = Form(...),
    valeur: str = Form(...),
    unite: str = Form(None),
    ordre: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        service.create_param_service(db, nom, valeur, unite, ordre)
        return RedirectResponse(url="/admin/params?success=1", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse("admin/params/create_param.html", {
            "request": request,
            "user": current_user,
            "error": str(e)
        })


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_param_form(id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    param = service.get_param_id(db, id)
    if not param:
        raise HTTPException(status_code=404, detail="Paramètre introuvable")
    return templates.TemplateResponse("admin/params/edit_param.html", {
        "request": request,
        "user": current_user,
        "param": param
    })


@router.post("/{id}/edit")
def update_param_action(
    id: int,
    request: Request,
    nom: str = Form(...),
    valeur: str = Form(...),
    unite: str = Form(None),
    ordre: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    try:
        updated = service.update_param_value(db, id, nom, valeur, unite, ordre)
        if not updated:
            raise HTTPException(status_code=404, detail="Paramètre introuvable")
        return RedirectResponse(url="/admin/params?updated=1", status_code=303)
    except ValueError as e:
        param = service.get_param_id(db, id)
        return templates.TemplateResponse("admin/params/edit_param.html", {
            "request": request,
            "param": param,
            "user": current_user,
            "error": str(e)
        })


@router.get("/json", response_model=List[ParamGeneral])
def list_params_json(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    return service.list_all_params(db)
