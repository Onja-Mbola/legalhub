import os
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cassation import CassationCreate, CassationUpdate
from app.services.cassation_service import (
    create_cassation_service,
    get_cassation_service,
    get_cassations_by_dossier_service,
    update_cassation_service,
    delete_cassation_service
)
from app.services.dossier import get_dossier_by_id
from app.services.fond_service import get_decision_fond_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/cassations", response_class=HTMLResponse)
def list_cassations(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    cassations = get_cassations_by_dossier_service(db, dossier_id)
    now_dt = datetime.now().date()

    return templates.TemplateResponse("avocat/cassation/list.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "cassations": cassations,
        "now": now_dt
    })


@router.get("/decisions_fond/{decision_fond_id}/cassation/create", response_class=HTMLResponse)
def form_create_cassation(
        decision_fond_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision_fond = get_decision_fond_service(db, decision_fond_id)
    dossier = get_dossier_by_id(db, decision_fond.dossier_id)

    if decision_fond.type_decision_fond != "contradictoire":
        raise HTTPException(
            status_code=400,
            detail="La cassation n'est possible que pour les décisions contradictoires"
        )

    return templates.TemplateResponse("avocat/cassation/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "decision_fond": decision_fond,
        "mode": "create"
    })


@router.get("/cassations/{cassation_id}", response_class=HTMLResponse)
def detail_cassation(
        cassation_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    cassation = get_cassation_service(db, cassation_id)
    dossier = get_dossier_by_id(db, cassation.dossier_id)
    now_dt = datetime.now().date()

    return templates.TemplateResponse("avocat/cassation/detail.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "cassation": cassation,
        "now": now_dt
    })


@router.get("/cassations/{cassation_id}/update", response_class=HTMLResponse)
def form_update_cassation(
        cassation_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    cassation = get_cassation_service(db, cassation_id)
    dossier = get_dossier_by_id(db, cassation.dossier_id)

    return templates.TemplateResponse("avocat/cassation/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "cassation": cassation,
        "mode": "update"
    })


def parse_optional_date(d: str | None) -> Optional[date]:
    if not d or d == "":
        return None
    return datetime.strptime(d, "%Y-%m-%d").date()


@router.post("/decisions_fond/{decision_fond_id}/cassation")
async def create_cassation(
        request: Request,
        decision_fond_id: int,
        date_notification_decision: str = Form(...),
        date_depot_requete: Optional[str] = Form(None),
        observations: Optional[str] = Form(None),
        copie_requete: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    decision_fond = get_decision_fond_service(db, decision_fond_id)
    dossier = get_dossier_by_id(db, decision_fond.dossier_id)

    date_notification_decision = parse_optional_date(date_notification_decision)
    date_depot_requete = parse_optional_date(date_depot_requete)
    statut = "requete_deposee" if date_depot_requete else "en_attente_requete"

    try:
        data = CassationCreate(
            decision_fond_id=decision_fond_id,
            dossier_id=dossier.id,
            date_notification_decision=date_notification_decision,
            date_depot_requete=date_depot_requete,
            statut=statut,
            observations=observations,
            # copie_requete=None
        )
        create_cassation_service(
            db, data, user.id, copie_requete=copie_requete
        )
        return RedirectResponse(
            url=f"/dossiers/{dossier.id}/cassations?success=1",
            status_code=303
        )
    except ValidationError as e:
        return templates.TemplateResponse("avocat/cassation/form.html", {
            "request": request,
            "user": user,
            "dossier": dossier,
            "decision_fond": decision_fond,
            "mode": "create",
            "errors": e.errors()
        })


@router.post("/cassations/{cassation_id}/update")
async def update_cassation(
        request: Request,
        cassation_id: int,
        date_notification_decision: Optional[str] = Form(None),
        date_depot_requete: Optional[str] = Form(None),
        date_depot_memoire_ampliatif: Optional[str] = Form(None),
        date_reception_memoire_defense: Optional[str] = Form(None),
        date_delibere: Optional[str] = Form(None),
        statut: Optional[str] = Form(None),
        observations: Optional[str] = Form(None),
        copie_requete: Optional[UploadFile] = File(None),
        copie_memoire_ampliatif: Optional[UploadFile] = File(None),
        copie_memoire_defense: Optional[UploadFile] = File(None),
        copie_reponse: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    cassation = get_cassation_service(db, cassation_id)
    dossier = get_dossier_by_id(db, cassation.dossier_id)

    try:
        data = CassationUpdate(
            date_notification_decision=parse_optional_date(date_notification_decision),
            date_depot_requete=parse_optional_date(date_depot_requete),
            date_depot_memoire_ampliatif=parse_optional_date(date_depot_memoire_ampliatif),
            date_reception_memoire_defense=parse_optional_date(date_reception_memoire_defense),
            date_delibere=parse_optional_date(date_delibere),
            statut=statut,
            observations=observations,
            # Fichiers=None
        )
        update_cassation_service(
            db, cassation_id, data, user.id,
            copie_requete=copie_requete,
            copie_memoire_ampliatif=copie_memoire_ampliatif,
            copie_memoire_defense=copie_memoire_defense,
            copie_reponse=copie_reponse
        )
        return RedirectResponse(
            url=f"/cassations/{cassation_id}?updated=1",
            status_code=303
        )
    except ValidationError as e:
        return templates.TemplateResponse("avocat/cassation/form.html", {
            "request": request,
            "user": user,
            "dossier": dossier,
            "cassation": cassation,
            "mode": "update",
            "errors": e.errors()
        })


@router.post("/cassations/{cassation_id}/delete")
async def delete_cassation(
        cassation_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    cassation = get_cassation_service(db, cassation_id)
    dossier_id = cassation.dossier_id

    delete_cassation_service(db, cassation_id, user.id)

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/cassations?deleted=1",
        status_code=303
    )
