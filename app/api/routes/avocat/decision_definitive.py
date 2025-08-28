from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import date

from app.core.auth import get_current_avocat_user
from app.core.jugement_enum import JugementType
from app.db.session import get_db
from app.models.user import User
from app.models.dossier import Dossier
from app.services.dossier import get_dossier_by_id
from app.schemas.decision_definitive import DecisionDefinitiveCreate
from app.services.decision_definitive_service import save_or_update_decision_definitive, \
    get_decision_definitive_by_dossier_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(404, "Dossier introuvable")
    return dossier


@router.get("/dossiers/{dossier_id}/decision_def", response_class=HTMLResponse)
def def_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = _get_dossier_or_404(db, dossier_id)
    decision  = get_decision_definitive_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse("avocat/decision_def/form.html", {
        "request": request,
        "user": user,
        "dossier": dossier,
        "items": decision,
        "JugementType": JugementType
    })

@router.post("/dossiers/{dossier_id}/decision_def")
async def def_create(
        dossier_id: int,
        date_decision: date = Form(...),
        type_decision: str = Form(...),
        motivation: Optional[str] = Form(None),
        jugement_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = _get_dossier_or_404(db, dossier_id)
    data = DecisionDefinitiveCreate(
        dossier_id=dossier_id,
        date_decision=date_decision,
        type_decision=type_decision,
        motivation=motivation
    )

    save_or_update_decision_definitive(db, dossier_id, user.nom, data, jugement_file)

    return RedirectResponse(url=f"/dossiers/?decision_finale=1", status_code=303)
