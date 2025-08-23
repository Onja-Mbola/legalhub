from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import date

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.models.dossier import Dossier
from app.services.dossier import get_dossier_by_id
from app.schemas.decision_avant_dire_droit import DecisionAvantDireDroitCreate, DecisionAvantDireDroitUpdate
from app.services.decision_avant_dire_droit_service import (
    create_decision_avant_dire_droit_service,
    update_decision_avant_dire_droit_service,
    get_decision_avant_dire_droit_by_dossier_service,
    get_decision_avant_dire_droit_by_id_service
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(404, "Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/decision_add", response_class=HTMLResponse)
def add_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    items = get_decision_avant_dire_droit_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/decision_add/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "items": items
    })


@router.get("/dossiers/{dossier_id}/decision_add_update/{decision_id}", response_class=HTMLResponse)
def update_form(
        dossier_id: int,
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    item = get_decision_avant_dire_droit_by_id_service(db, decision_id)
    return templates.TemplateResponse("avocat/decision_add/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "item": item
    })


@router.post("/dossiers/{dossier_id}/decision_add")
async def decision_add_create(
        dossier_id: int,
        date_decision: date = Form(...),
        nature_incident: str = Form(...),
        contenu: Optional[str] = Form(None),
        ordonnance_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = DecisionAvantDireDroitCreate(
        dossier_id=dossier_id,
        date_decision=date_decision,
        nature_incident=nature_incident,
        contenu=contenu
    )

    create_decision_avant_dire_droit_service(db, dossier_id, user.nom, data, ordonnance_file)

    return RedirectResponse(url=f"/dossiers/?add_success=1", status_code=303)


@router.post("/dossiers/{dossier_id}/decision_add_update/{decision_id}")
async def decision_add_update(
        dossier_id: int,
        decision_id: int,
        date_decision: date = Form(...),
        nature_incident: str = Form(...),
        contenu: Optional[str] = Form(None),
        ordonnance_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    data = DecisionAvantDireDroitUpdate(
        date_decision=date_decision,
        nature_incident=nature_incident,
        contenu=contenu
    )

    update_decision_avant_dire_droit_service(db, decision_id, user.nom, data, ordonnance_file)

    return RedirectResponse(url=f"/dossiers/?update_success=1", status_code=303)
