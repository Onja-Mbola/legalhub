from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.premiere_audience_service import get_by_dossier, insert_or_update_premiere_audience_with_file, \
    get_premiere_audience_by_id
from app.services.requete_assignation import get_requete_assignation_by_dossier_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/premiere_audience", response_class=HTMLResponse)
def premiere_audience_form(
    dossier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user),
):
    premiere_audience = get_premiere_audience_by_id(db, dossier_id)
    return templates.TemplateResponse("avocat/premiere_audience/form.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "premiere_audience": premiere_audience
    })


@router.post("/dossiers/{dossier_id}/premiere_audience")
async def create_or_update_premiere_audience(
    request: Request,
    dossier_id: int,
    decision: Optional[str] = Form(None),
    nouvelle_date_audience: str = Form(...),
    nom_judge: Optional[str] = Form(None),
    observations_judge: Optional[str] = Form(None),
    observations_internes: Optional[str] = Form(None),
    pv_audience: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user)
):
    error_msg = None
    try:
        requete_assignation = get_requete_assignation_by_dossier_service(db, dossier_id)
        if not requete_assignation:
            error_msg = "Impossible de créer la Première Audience : La Requête & Assignation n'a pas encore été fait."
            raise ValueError(error_msg)
        insert_or_update_premiere_audience_with_file(
            db=db,
            dossier_id=int(dossier_id),
            avocat_nom=user.nom,
            decision=decision,
            nouvelle_date_audience=nouvelle_date_audience,
            nom_judge=nom_judge,
            observations_judge=observations_judge,
            observations_internes=observations_internes,
            pv_audience=pv_audience
        )
    except Exception as e:
        return templates.TemplateResponse(
            "avocat/premiere_audience/form.html",
            {
                "request": request,
                "user": user,
                "error_msg": str(e),
            },
        )

    return RedirectResponse(url="/dossiers?premiere_audience_success=1", status_code=303)
