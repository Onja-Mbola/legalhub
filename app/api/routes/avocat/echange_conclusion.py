from typing import Optional, List
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
from app.schemas.echange_conclusion import EchangeConclusionCreate, EchangeConclusionUpdate
from app.services.echange_conclusion_service import (
    create_echange_conclusion_service,
    update_echange_conclusion_service,
    get_echange_conclusion_by_dossier_service,
    get_echange_conclusion_by_id, create_echange_conclusion_service_retour_audience
)
from app.services.retour_audience_service import get_retour_audience_by_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/echange_conclusions", response_class=HTMLResponse)
def echange_form_create(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    items = get_echange_conclusion_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/echange_conclusions/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "items": items,
        "mode": "create"
    })


@router.get("/dossiers/{dossier_id}/echange_conclusions/retour_audience/{retour_audience_id}", response_class=HTMLResponse)
def echange_form_create_retour_audience(
        dossier_id: int,
        retour_audience_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    retour_audience = get_retour_audience_by_id(db, retour_audience_id)
    items = get_echange_conclusion_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/echange_conclusions/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "items": items,
        "retour_audience": retour_audience,
        "mode": "creates"
    })


@router.get("/dossiers/{dossier_id}/echange_conclusions/{echange_id}/update", response_class=HTMLResponse)
def echange_form_update(
        dossier_id: int,
        echange_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    item = get_echange_conclusion_by_id(db, echange_id)
    if not item:
        raise HTTPException(status_code=404, detail="Échange de conclusion introuvable")
    return templates.TemplateResponse("avocat/echange_conclusions/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "item": item,
        "mode": "update"
    })


@router.post("/dossiers/{dossier_id}/echange_conclusions")
async def echange_create(
        dossier_id: int,
        partie: str = Form(...),
        date_depot: date = Form(...),
        contenu_resume: Optional[str] = Form(None),
        motif_renvoi: Optional[str] = Form(None),
        conclusions_file: List[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = EchangeConclusionCreate(
        dossier_id=dossier_id,
        partie=partie,
        date_depot=date_depot,
        contenu_resume=contenu_resume,
        motif_renvoi=motif_renvoi
    )

    create_echange_conclusion_service(db, dossier_id, user.nom, data, conclusions_file)

    return RedirectResponse(url=f"/dossiers/?echange_success=1", status_code=303)


@router.post("/dossiers/{dossier_id}/echange_conclusions/retour_audience/{retour_audience_id}")
async def echange_create_retour_audience(
        dossier_id: int,
        retour_audience_id: int,
        partie: str = Form(...),
        date_depot: date = Form(...),
        contenu_resume: Optional[str] = Form(None),
        motif_renvoi: Optional[str] = Form(None),
        conclusions_file: List[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = EchangeConclusionCreate(
        dossier_id=dossier_id,
        retour_audience_id=retour_audience_id,
        partie=partie,
        date_depot=date_depot,
        contenu_resume=contenu_resume,
        motif_renvoi=motif_renvoi
    )

    create_echange_conclusion_service_retour_audience(db, dossier_id, user.nom, data, conclusions_file)

    return RedirectResponse(url=f"/dossiers/?echange_retour_success=1", status_code=303)

@router.post("/dossiers/{dossier_id}/echange_conclusions/{echange_id}/update")
async def echange_update(
        dossier_id: int,
        echange_id: int,
        partie: str = Form(...),
        date_depot: date = Form(...),
        contenu_resume: Optional[str] = Form(None),
        motif_renvoi: Optional[str] = Form(None),
        conclusions_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = EchangeConclusionUpdate(
        partie=partie,
        date_depot=date_depot,
        contenu_resume=contenu_resume,
        motif_renvoi=motif_renvoi
    )

    update_echange_conclusion_service(db, echange_id, data, conclusions_file, user.nom)

    return RedirectResponse(url=f"/dossiers/?echange_updated=1", status_code=303)
