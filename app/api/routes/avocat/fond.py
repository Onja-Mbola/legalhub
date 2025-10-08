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
from app.schemas.fond import DecisionFondCreate, DecisionFondUpdate
from app.services.fond_service import (
    create_decision_fond_service,
    get_decision_fond_service,
    get_decisions_by_dossier_service,
    get_decisions_par_defaut_service,
    get_decisions_contradictoires_service,
    update_decision_fond_service,
    delete_decision_fond_service
)
from app.services.dossier import get_dossier_by_id
from app.services.FileStorageService import storage
from app.services.nlp_service import extract_entities
from app.services.ocr_service import perform_ocr, anonymize_text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/decisions_fond", response_class=HTMLResponse)
def list_decisions_fond(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    decisions = get_decisions_by_dossier_service(db, dossier_id)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/fond/list.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decisions": decisions,
        "now": now_dt
    })


@router.get("/decisions_fond/par_defaut", response_class=HTMLResponse)
def list_decisions_par_defaut(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decisions = get_decisions_par_defaut_service(db)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/fond/list_filtered.html", {
        "request": request,
        "user": user,
        "decisions": decisions,
        "filter_type": "par_defaut",
        "title": "Décisions par Défaut",
        "now": now_dt
    })


@router.get("/decisions_fond/contradictoires", response_class=HTMLResponse)
def list_decisions_contradictoires(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decisions = get_decisions_contradictoires_service(db)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/fond/list_filtered.html", {
        "request": request,
        "user": user,
        "decisions": decisions,
        "filter_type": "contradictoire",
        "title": "Décisions Contradictoires",
        "now": now_dt
    })


@router.get("/dossiers/{dossier_id}/deliberation/{deliberation_id}/decision_fond/create", response_class=HTMLResponse)
def form_create_decision_fond(
        dossier_id: int,
        deliberation_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    return templates.TemplateResponse("avocat/fond/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "deliberation_id": deliberation_id,
        "mode": "create"
    })


@router.get("/decisions_fond/{decision_id}", response_class=HTMLResponse)
def detail_decision_fond(
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_fond_service(db, decision_id)
    dossier = _get_dossier_or_404(db, decision.dossier_id)
    now_dt = datetime.now().date()
    return templates.TemplateResponse("avocat/fond/detail.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decision": decision,
        "now": now_dt
    })


@router.get("/decisions_fond/{decision_id}/update", response_class=HTMLResponse)
def form_update_decision_fond(
        decision_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_fond_service(db, decision_id)
    dossier = _get_dossier_or_404(db, decision.dossier_id)
    return templates.TemplateResponse("avocat/fond/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decision": decision,
        "mode": "update"
    })


@router.post("/dossiers/{dossier_id}/deliberation/{deliberation_id}/decision_fond")
async def create_decision_fond(
        dossier_id: int,
        deliberation_id: int,
        date_decision_fond: date = Form(...),
        type_decision_fond: str = Form(...),
        sens_decision: Optional[str] = Form(None),
        texte_decision: Optional[str] = Form(None),
        date_notification: Optional[date] = Form(None),
        delai_appel: int = Form(30),
        observations: Optional[str] = Form(None),
        copie_decision_fond: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)

    if date_notification and date_notification < date_decision_fond:
        raise HTTPException(
            status_code=400,
            detail="La date de notification ne peut pas être antérieure à la date de décision"
        )

    file_path = None

    data = DecisionFondCreate(
        dossier_id=dossier_id,
        deliberation_decision_id=deliberation_id,
        date_decision_fond=date_decision_fond,
        type_decision_fond=type_decision_fond,
        sens_decision=sens_decision,
        texte_decision=texte_decision,
        date_notification=date_notification,
        delai_appel=delai_appel,
        observations=observations,
        # copie_decision_fond=file_path
    )

    create_decision_fond_service(db, data, user.id, copie_decision_fond)

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/decisions_fond?success=1",
        status_code=303
    )


@router.post("/decisions_fond/{decision_id}/update")
async def update_decision_fond(
        decision_id: int,
        date_decision_fond: Optional[date] = Form(None),
        type_decision_fond: Optional[str] = Form(None),
        sens_decision: Optional[str] = Form(None),
        texte_decision: Optional[str] = Form(None),
        date_notification: Optional[date] = Form(None),
        delai_appel: Optional[int] = Form(None),
        observations: Optional[str] = Form(None),
        copie_decision_fond: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_fond_service(db, decision_id)

    file_path = None
    dossier = _get_dossier_or_404(db, decision.dossier_id)

    data = DecisionFondUpdate(
        date_decision_fond=date_decision_fond,
        type_decision_fond=type_decision_fond,
        sens_decision=sens_decision,
        texte_decision=texte_decision,
        date_notification=date_notification,
        delai_appel=delai_appel,
        observations=observations,
        # copie_decision_fond=file_path if file_path else None
    )

    update_decision_fond_service(db, decision_id, data, user.id, copie_decision_fond)

    return RedirectResponse(
        url=f"/decisions_fond/{decision_id}?updated=1",
        status_code=303
    )


@router.post("/decisions_fond/{decision_id}/delete")
async def delete_decision_fond(
        decision_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision = get_decision_fond_service(db, decision_id)
    dossier_id = decision.dossier_id

    delete_decision_fond_service(db, decision_id)

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/decisions_fond?deleted=1",
        status_code=303
    )