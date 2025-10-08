from datetime import datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.enrolement import get_enrolement_by_dossier_service
from app.services.premiere_audience_appel_service import (
    get_premiere_audience_appel_by_dossier_service,
    insert_premiere_audience_appel_with_file
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/premiere_audience_appel", response_class=HTMLResponse)
def premiere_audience_appel_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    enrolement_appel = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)
    if not enrolement_appel:
        raise HTTPException(
            status_code=404,
            detail="Enrôlement d'appel non trouvé pour ce dossier"
        )

    premiere_audience_appel = get_premiere_audience_appel_by_dossier_service(db, dossier_id)

    return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "enrolement_appel": enrolement_appel,
        "premiere_audience_appel": premiere_audience_appel
    })


@router.post("/dossiers/{dossier_id}/premiere_audience_appel")
async def create_or_update_premiere_audience_appel(
        request: Request,
        dossier_id: int,
        enrolement_appel_id: int = Form(...),
        date_audience: str = Form(...),
        heure_audience: Optional[str] = Form(None),
        lieu_audience: Optional[str] = Form(None),
        juge_rapporteur: Optional[str] = Form(None),
        observations: Optional[str] = Form(None),
        convocation_recue: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    enrolement_appel = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)
    premiere_audience_appel = get_premiere_audience_appel_by_dossier_service(db, dossier_id)

    try:
        date_audience_obj = datetime.strptime(date_audience, "%Y-%m-%d").date()
    except ValueError:
        error_msg = "La date d’audience est invalide (format attendu : AAAA-MM-JJ)."
        return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement_appel": enrolement_appel,
            "premiere_audience_appel": premiere_audience_appel,
            "error_msg": error_msg
        })

    enrolement_date = None
    if enrolement_appel:
        enrolement_date = enrolement_appel[0].date_enrolement if isinstance(enrolement_appel,
                                                                            list) else enrolement_appel.date_enrolement

    if enrolement_date and date_audience_obj <= enrolement_date:
        error_msg = (
            f"La date d’audience ({date_audience_obj.strftime('%d/%m/%Y')}) "
            f"doit être postérieure à la date d’enrôlement ({enrolement_date.strftime('%d/%m/%Y')})."
        )
        return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement_appel": enrolement_appel,
            "premiere_audience_appel": premiere_audience_appel,
            "error_msg": error_msg
        })

    if heure_audience:
        try:
            heure_obj = datetime.strptime(heure_audience, "%H:%M").time()
            if heure_obj < time(7, 0) or heure_obj > time(18, 0):
                error_msg = "L’heure d’audience doit être comprise entre 07h00 et 18h00."
                return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
                    "request": request,
                    "user": user,
                    "dossier_id": dossier_id,
                    "enrolement_appel": enrolement_appel,
                    "premiere_audience_appel": premiere_audience_appel,
                    "error_msg": error_msg
                })
        except ValueError:
            error_msg = "L’heure d’audience est invalide (format attendu : HH:MM)."
            return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
                "request": request,
                "user": user,
                "dossier_id": dossier_id,
                "enrolement_appel": enrolement_appel,
                "premiere_audience_appel": premiere_audience_appel,
                "error_msg": error_msg
            })

    try:
        insert_premiere_audience_appel_with_file(
            db=db,
            dossier_id=dossier_id,
            avocat_nom=user.nom,
            enrolement_appel_id=enrolement_appel_id,
            date_audience_str=date_audience,
            heure_audience_str=heure_audience,
            lieu_audience=lieu_audience,
            juge_rapporteur=juge_rapporteur,
            observations=observations,
            convocation_file=convocation_recue
        )
    except Exception as e:
        return templates.TemplateResponse("avocat/premiere_audience_appel/form.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement_appel": enrolement_appel,
            "premiere_audience_appel": premiere_audience_appel,
            "error_msg": str(e)
        })

    return RedirectResponse(
        url="/dossiers?premiere_audience_appel_success=1",
        status_code=303
    )
