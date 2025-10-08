import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.models.dossier import Dossier
from app.schemas.avant_dire_droit import DecisionADDCreate, DecisionADDUpdate
from app.services.avant_dire_droit_service import (
    create_decision_add_service,
    get_decision_add_service,
    get_decisions_by_dossier_service,
    update_decision_add_service,
    delete_decision_add_service
)
from app.services.dossier import get_dossier_by_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/decisions_add", response_class=HTMLResponse)
def list_decisions_add(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    decisions = get_decisions_by_dossier_service(db, dossier_id)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/avant_dire_droit/list.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decisions": decisions,
        "now": now_dt
    })


@router.get("/dossiers/{dossier_id}/deliberation/{deliberation_id}/decision_add/create", response_class=HTMLResponse)
def form_create_decision_add(
        dossier_id: int,
        deliberation_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    return templates.TemplateResponse("avocat/avant_dire_droit/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "deliberation_id": deliberation_id,
        "mode": "create"
    })


@router.get("/decisions_add/{decision_id}", response_class=HTMLResponse)
def detail_decision_add(
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_add_service(db, decision_id)
    dossier = _get_dossier_or_404(db, decision.dossier_id)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/avant_dire_droit/detail.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decision": decision,
        "now": now_dt
    })


@router.get("/decisions_add/{decision_id}/update", response_class=HTMLResponse)
def form_update_decision_add(
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_add_service(db, decision_id)
    dossier = _get_dossier_or_404(db, decision.dossier_id)

    return templates.TemplateResponse("avocat/avant_dire_droit/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decision": decision,
        "mode": "update"
    })


@router.post("/dossiers/{dossier_id}/deliberation/{deliberation_id}/decision_add")
async def create_decision_add(
        dossier_id: int,
        deliberation_id: int,
        date_decision_add: date = Form(...),
        motif_renvoi: Optional[str] = Form(None),
        delai_conclusions: Optional[int] = Form(None),
        observations: Optional[str] = Form(None),
        copie_decision_add: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)

    data = DecisionADDCreate(
        dossier_id=dossier_id,
        deliberation_decision_id=deliberation_id,
        date_decision_add=date_decision_add,
        motif_renvoi=motif_renvoi,
        delai_conclusions=delai_conclusions,
        observations=observations,
        # copie_decision_add=None
    )

    create_decision_add_service(db, data, user.id, copie_decision_add=copie_decision_add)

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/decisions_add?success=1",
        status_code=303
    )


@router.post("/decisions_add/{decision_id}/update")
async def update_decision_add(
        decision_id: int,
        date_decision_add: Optional[date] = Form(None),
        motif_renvoi: Optional[str] = Form(None),
        delai_conclusions: Optional[int] = Form(None),
        observations: Optional[str] = Form(None),
        copie_decision_add: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_add_service(db, decision_id)
    dossier = _get_dossier_or_404(db, decision.dossier_id)

    data = DecisionADDUpdate(
        date_decision_add=date_decision_add,
        motif_renvoi=motif_renvoi,
        delai_conclusions=delai_conclusions,
        observations=observations,
        # copie_decision_add=None
    )

    update_decision_add_service(db, decision_id, data, user.id, copie_decision_add=copie_decision_add)

    return RedirectResponse(
        url=f"/decisions_add/{decision_id}?updated=1",
        status_code=303
    )


@router.post("/decisions_add/{decision_id}/delete")
async def delete_decision_add(
        decision_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_add_service(db, decision_id)
    dossier_id = decision.dossier_id

    delete_decision_add_service(db, decision_id)

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/decisions_add?deleted=1",
        status_code=303
    )
