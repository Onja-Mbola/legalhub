from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.retour_audience_service import (
    insert_or_update_retour_audience_with_file,
    get_by_dossier,
    get_retour_audience_by_id
)
from app.services.jugement_service import get_jugement_by_dossier_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/retour_audience", response_class=HTMLResponse)
def retour_audience_form(
    dossier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user),
):
    retour_audience = get_by_dossier(db, dossier_id)
    retour_audience = retour_audience[0] if retour_audience else None
    return templates.TemplateResponse("avocat/retour_audience/form.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "retour_audience": retour_audience
    })


@router.post("/dossiers/{dossier_id}/retour_audience")
async def create_or_update_retour_audience(
    request: Request,
    dossier_id: int,
    date_audience: str = Form(...),
    nom_judge: Optional[str] = Form(None),
    observations_judge: Optional[str] = Form(None),
    observations_internes: Optional[str] = Form(None),
    pv_audience: Optional[UploadFile] = File(None),
    jugement_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user)
):
    error_msg = None
    try:
        jugement = get_jugement_by_dossier_service(db, dossier_id)
        if not jugement:
            error_msg = "Impossible d'enregistrer le retour d'audience : Aucun jugement trouvé pour ce dossier."
            raise ValueError(error_msg)

        insert_or_update_retour_audience_with_file(
            db=db,
            dossier_id=int(dossier_id),
            avocat_nom=user.nom,
            date_audience=datetime.fromisoformat(date_audience),
            nom_judge=nom_judge,
            observations_judge=observations_judge,
            observations_internes=observations_internes,
            pv_audience=pv_audience,
            jugement_id=jugement_id
        )
    except Exception as e:
        return templates.TemplateResponse(
            "avocat/retour_audience/form.html",
            {
                "request": request,
                "user": user,
                "error_msg": str(e),
            },
        )

    return RedirectResponse(url="/dossiers?retour_audience_success=1", status_code=303)
