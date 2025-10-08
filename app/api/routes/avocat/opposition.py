import os
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user
from app.core.workflow_enums import ProcessStage
from app.db.session import get_db
from app.models.user import User
from app.models.opposition import Opposition
from app.repositories.dossier import get_dossier_by_id
from app.schemas.opposition import OppositionUpdate
from app.services.FileStorageService import storage
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.nlp_service import extract_entities
from app.services.ocr_service import perform_ocr, anonymize_text
from app.services.opposition_service import (
    create_opposition_service,
    get_oppositions_by_dossier_service,
    get_opposition_service,
    update_opposition_service,
    update_opposition_appel_service,
)
from app.services.workflow_guard import WorkflowGuard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


@router.get("/dashboard/oppositions")
def dashboard_oppositions(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    total = db.query(Opposition).count()

    en_cours = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua >= date.today()
    ).count()

    expirees = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua < date.today()
    ).count()

    formulees = db.query(Opposition).filter(
        Opposition.opposition_formulee == True
    ).count()

    oppositions_en_cours = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua >= date.today()
    ).all()

    oppositions_expirees = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua < date.today()
    ).all()

    oppositions_formulees = db.query(Opposition).filter(
        Opposition.opposition_formulee == True
    ).all()

    return templates.TemplateResponse(
        "avocat/opposition/dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": {
                "total": total,
                "en_cours": en_cours,
                "expirees_non_traitees": expirees,
                "formulees": formulees
            },
            "oppositions_en_cours": oppositions_en_cours,
            "oppositions_expirees": oppositions_expirees,
            "oppositions_formulees": oppositions_formulees,
            "today": date.today()
        }
    )


@router.get("/api/dashboard/oppositions")
def api_dashboard_oppositions(db: Session = Depends(get_db)):
    total = db.query(Opposition).count()
    en_cours = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua >= date.today()
    ).count()
    expirees = db.query(Opposition).filter(
        Opposition.opposition_formulee == False,
        Opposition.opposition_possible_jusqua < date.today()
    ).count()
    formulees = db.query(Opposition).filter(
        Opposition.opposition_formulee == True
    ).count()

    return JSONResponse({
        "total": total,
        "en_cours": en_cours,
        "expirees_non_traitees": expirees,
        "formulees": formulees
    })


@router.get("/dossiers/{dossier_id}/opposition")
def form_opposition(
        request: Request,
        dossier_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    WorkflowGuard.advance(dossier, ProcessStage.PAR_DEFAUT, db)

    log_action_service(
        db, user.id,
        "Création jugement par défaut",
        f"Création du jugement par défaut pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    oppositions = get_oppositions_by_dossier_service(db, dossier_id)

    return templates.TemplateResponse(
        "avocat/opposition/opposition_form.html",
        {
            "request": request,
            "dossier": dossier,
            "user": user,
            "oppositions": oppositions,
        }
    )


@router.post("/dossiers/{dossier_id}/opposition")
def save_opposition(
        dossier_id: int,
        jugement_id: int = Form(...),
        date_notification: str = Form(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    date_notification_parsed = datetime.strptime(date_notification, "%Y-%m-%d")

    create_opposition_service(
        db=db,
        dossier_id=dossier_id,
        jugement_id=jugement_id,
        date_notification=date_notification_parsed,
    )

    return RedirectResponse(url=f"/dossiers?opposition_success=1", status_code=303)


@router.get("/dossiers/opposition/{opposition_id}/edit")
def edit_opposition_form(
        request: Request,
        opposition_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    opposition = get_opposition_service(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition introuvable")

    today = datetime.now().date()
    delai_depasse = today > opposition.opposition_possible_jusqua

    return templates.TemplateResponse(
        "avocat/opposition/opposition_edit.html",
        {
            "request": request,
            "user": user,
            "opposition": opposition,
            "delai_depasse": delai_depasse,
        }
    )


@router.post("/dossiers/opposition/{opposition_id}/edit")
def update_opposition(
        opposition_id: int,
        date_notification: str = Form(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    date_notification_parsed = datetime.strptime(date_notification, "%Y-%m-%d")

    update_data = OppositionUpdate(
        date_notification=date_notification_parsed,
    )

    update_opposition_service(db, opposition_id, update_data)

    return RedirectResponse(
        url=f"/dossiers/opposition/{opposition_id}/edit?success=1",
        status_code=303
    )


@router.get("/oppositions/{opposition_id}/formuler")
def form_formuler_opposition(
        request: Request,
        opposition_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    opposition = get_opposition_service(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition introuvable")

    if not opposition.decision_fond_id:
        raise HTTPException(
            status_code=400,
            detail="Cette opposition n'est pas liée à une décision par défaut"
        )

    today = datetime.now().date()
    if today > opposition.opposition_possible_jusqua:
        raise HTTPException(
            status_code=400,
            detail=f"Le délai d'opposition est dépassé (limite: {opposition.opposition_possible_jusqua})"
        )

    return templates.TemplateResponse(
        "avocat/opposition/opposition_formuler.html",
        {
            "request": request,
            "user": user,
            "opposition": opposition,
            "datetime_now": datetime.utcnow().date()
    }
    )


@router.post("/oppositions/{opposition_id}/formuler")
async def formuler_opposition(
        opposition_id: int,
        date_opposition: str = Form(...),
        acte_opposition: Optional[UploadFile] = File(None),
        motifs_opposition: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    date_opposition_parsed = datetime.strptime(date_opposition, "%Y-%m-%d").date()
    opposition = get_opposition_service(db, opposition_id)
    dossier = _get_dossier_or_404(db, opposition.dossier_id)

    if dossier.current_stage != ProcessStage.FOND.value:
        raise HTTPException(status_code=400, detail="Vous devez d'abord passer par la decision de fond.")

    updated_opposition = update_opposition_appel_service(
        db=db,
        opposition_id=opposition_id,
        date_opposition=date_opposition_parsed,
        acte_opposition_file=acte_opposition,
        motifs_opposition=motifs_opposition
    )

    WorkflowGuard.advance(dossier, ProcessStage.OPPOSITION, db)

    log_action_service(
        db, user.id,
        "Opposition formulée",
        f"Opposition formulée pour le dossier {updated_opposition.dossier.numero_dossier}",
        updated_opposition.dossier_id
    )

    return RedirectResponse(
        url=f"/dossiers/{updated_opposition.dossier_id}?opposition_formulee=1",
        status_code=303
    )
