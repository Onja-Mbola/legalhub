from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user
from app.core.workflow_enums import ProcessStage
from app.db.session import get_db
from app.models.user import User
from app.schemas.opposition import OppositionUpdate
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.opposition_service import (
    create_opposition_service,
    get_oppositions_by_dossier_service, get_opposition_service, update_opposition_service, )
from app.services.workflow_guard import WorkflowGuard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/opposition")
def form_opposition(request: Request, dossier_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_avocat_user)):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    WorkflowGuard.advance(dossier, ProcessStage.PAR_DEFAUT, db)
    log_action_service(db, user.id, "Création jugement par defaut",
                       f"Création du jugement par defaut pour le dossier {dossier.numero_dossier}",
                       dossier.id)

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

    return templates.TemplateResponse(
        "avocat/opposition/opposition_edit.html",
        {
            "request": request,
            "user": user,
            "opposition": opposition,
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
