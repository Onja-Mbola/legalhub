from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.dossier import Dossier
from app.models.user import User
from app.schemas.deliberation_decision import DeliberationDecisionCreate, DeliberationDecisionUpdate
from app.services.deliberation_decision_service import (
    create_deliberation_decision_service,
    update_deliberation_decision_service,
    get_deliberation_decision_by_dossier_service,
    get_deliberation_decision_by_id_service, create_deliberation_decision_service_retour_audience
)
from app.services.dossier import get_dossier_by_id
from app.services.retour_audience_service import get_retour_audience_by_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(404, "Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/deliberation", response_class=HTMLResponse)
def delib_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    items = get_deliberation_decision_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/deliberation_decision/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "items": items
    })

@router.get("/dossiers/{dossier_id}/deliberation/retour_audience/{retour_audience_id}", response_class=HTMLResponse)
def delib_form_retour_audience(
        dossier_id: int,
        retour_audience_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    retour_audience = get_retour_audience_by_id(db, retour_audience_id)
    items = get_deliberation_decision_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/deliberation_decision/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "retour_audience": retour_audience,
        "items": items
    })


@router.get("/dossiers/{dossier_id}/deliberation_update/{decision_id}", response_class=HTMLResponse)
def delib_update_form(
        dossier_id: int,
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    item = get_deliberation_decision_by_id_service(db, decision_id)
    return templates.TemplateResponse("avocat/deliberation_decision/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "item": item
    })


@router.post("/dossiers/{dossier_id}/deliberation")
async def delib_create(
        dossier_id: int,
        date_mise_en_delibere: date = Form(...),
        type_decision_attendue: str = Form(...),
        observations_juge: Optional[str] = Form(None),
        note_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = DeliberationDecisionCreate(
        dossier_id=dossier_id,
        date_mise_en_delibere=date_mise_en_delibere,
        type_decision_attendue=type_decision_attendue,
        observations_juge=observations_juge
    )

    create_deliberation_decision_service(db, dossier_id, user.nom, data, note_file)

    return RedirectResponse(url=f"/dossiers/?delib_success=1", status_code=303)


@router.post("/dossiers/{dossier_id}/deliberation/retour_audience/{retour_audience_id}")
async def delib_create_retour_audience(
        dossier_id: int,
        retour_audience_id: int,
        date_mise_en_delibere: date = Form(...),
        type_decision_attendue: str = Form(...),
        observations_juge: Optional[str] = Form(None),
        note_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = DeliberationDecisionCreate(
        dossier_id=dossier_id,
        retour_audience_id=retour_audience_id,
        date_mise_en_delibere=date_mise_en_delibere,
        type_decision_attendue=type_decision_attendue,
        observations_juge=observations_juge
    )

    create_deliberation_decision_service_retour_audience(db, dossier_id, user.nom, data, note_file)

    return RedirectResponse(url=f"/dossiers/?delib_retour_audience_success=1", status_code=303)

@router.post("/dossiers/{dossier_id}/deliberation_update/{decision_id}")
async def delib_update(
        decision_id: int,
        date_mise_en_delibere: date = Form(...),
        type_decision_attendue: str = Form(...),
        observations_juge: Optional[str] = Form(None),
        note_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    data = DeliberationDecisionUpdate(
        date_mise_en_delibere=date_mise_en_delibere,
        type_decision_attendue=type_decision_attendue,
        observations_juge=observations_juge
    )

    update_deliberation_decision_service(db, decision_id, user.nom, data, note_file)

    return RedirectResponse(url=f"/dossiers/?delib_update_success=1", status_code=303)
