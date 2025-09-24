from datetime import date

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.core.workflow_enums import ProcessStage
from app.db.session import get_db
from app.models.dossier import Dossier
from app.models.user import User
from app.schemas.appel import AppelCreate, AppelUpdate
from app.services.action_log import log_action_service
from app.services.appel_service import (
    create_appel_service,
    update_appel_service,
    get_appel_service,
    get_appels_for_dossier_service,
    delete_appel_service
)
from app.services.dossier import get_dossier_by_id_service
from app.services.param_general import get_param_ordered, to_dict_list
from app.services.workflow_guard import WorkflowGuard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/appels", response_class=HTMLResponse)
def appel_list(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    appels = get_appels_for_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/appels/list.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "appels": appels
    })


@router.get("/dossiers/{dossier_id}/appels/create", response_class=HTMLResponse)
def appel_form_create(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    if dossier.current_stage != ProcessStage.JUGEMENT_CONTRADICTOIRE.value:
        WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_CONTRADICTOIRE, db)
    log_action_service(db, user.id, "Création jugement contradictoire",
                       f"Création du jugement contradictoire pour le dossier {dossier.numero_dossier}",
                       dossier.id)
    return templates.TemplateResponse("avocat/appels/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "mode": "create"
    })


@router.post("/dossiers/{dossier_id}/appels/create")
def appel_create(
        dossier_id: int,
        request: Request,
        motif: str = Form(...),
        date_depot: date = Form(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = AppelCreate(dossier_id=dossier_id, motif=motif, date_depot=date_depot)

    try:
        create_appel_service(db, dossier_id, user.id, data)
    except HTTPException as e:
        return templates.TemplateResponse("avocat/appels/form.html", {
            "request": request,
            "user": user,
            "dossier": dossier,
            "mode": "create",
            "error_msg": e.detail + "-"
        })
    except Exception as e:
        return templates.TemplateResponse("avocat/appels/form.html", {
            "request": request,
            "user": user,
            "dossier": dossier,
            "mode": "create",
            "error_msg": str(e)
        })

    return RedirectResponse(url=f"/dossiers/{dossier_id}/appels?success=1", status_code=303)


@router.get("/dossiers/{dossier_id}/appels/{appel_id}/update", response_class=HTMLResponse)
def appel_form_update(
        dossier_id: int,
        appel_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    appel = get_appel_service(db, appel_id)
    sous_type_options = get_param_ordered(db, "statut_appel", "asc")
    return templates.TemplateResponse("avocat/appels/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "appel": appel,
        "mode": "update",
        "sous_type_options": to_dict_list(sous_type_options)
    })


@router.post("/dossiers/{dossier_id}/appels/{appel_id}/update")
def appel_update(
        dossier_id: int,
        appel_id: int,
        request: Request,
        motif: str = Form(...),
        statut: str = Form(...),
        date_depot: date = Form(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    data = AppelUpdate(motif=motif, date_depot=date_depot, statut=statut)
    try:
        update_appel_service(db, appel_id, user.id, data)
    except HTTPException as e:
        dossier = _get_dossier_or_404(db, dossier_id)
        appel = get_appel_service(db, appel_id)
        sous_type_options = get_param_ordered(db, "statut_appel", "asc")
        return templates.TemplateResponse("avocat/appels/form.html", {
            "request": request,
            "user": user,
            "dossier": dossier,
            "appel": appel,
            "mode": "update",
            "error_msg": e.detail,
            "sous_type_options": to_dict_list(sous_type_options)
        })

    return RedirectResponse(url=f"/dossiers/{dossier_id}/appels?updated=1", status_code=303)


@router.post("/dossiers/{dossier_id}/appels/{appel_id}/delete")
def appel_delete(
        dossier_id: int,
        appel_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:
        delete_appel_service(db, appel_id, user.id)
    except HTTPException as e:
        return {"error": e.detail}
    return RedirectResponse(url=f"/dossiers/?deleted_appel=1", status_code=303)
