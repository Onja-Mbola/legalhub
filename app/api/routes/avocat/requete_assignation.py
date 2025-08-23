from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.requete_assignation import RequeteAssignationCreate, RequeteAssignationUpdate
from app.services.enrolement import get_enrolement_by_dossier_service
from app.services.requete_assignation import (
    get_requete_assignation_by_dossier_service,
    create_requete_assignation_service,
    update_requete_assignation_service,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/requete_assignation", response_class=HTMLResponse)
def requete_assignation_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    requete_assignation = get_requete_assignation_by_dossier_service(db, dossier_id)
    if not requete_assignation:
        requete_assignation = None
    return templates.TemplateResponse(
        "avocat/requete_assignation/form.html",
        {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "requete_assignation": requete_assignation,
        },
    )


@router.post("/dossiers/{dossier_id}/requete_assignation", response_class=HTMLResponse)
async def create_or_update_requete_assignation(
        request: Request,
        dossier_id: int,
        nom_huissier: str = Form(...),
        date_signification: str = Form(...),
        date_audience: str = Form(...),
        assignation_file: Optional[UploadFile] = File(None),
        preuve_signification_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    requete_assignation = get_requete_assignation_by_dossier_service(db, dossier_id)
    error_msg = None

    date_signification_dt = datetime.strptime(date_signification, "%Y-%m-%d").date()
    date_audience_dt = datetime.strptime(date_audience, "%Y-%m-%d").date()

    if requete_assignation:
        data = RequeteAssignationUpdate(
            nom_huissier=nom_huissier,
            date_signification=date_signification_dt,
            date_audience=date_audience_dt,
        )
        update_requete_assignation_service(
            db=db,
            db_obj=requete_assignation,
            avocat_nom=user.nom,
            dossier_id=dossier_id,
            data=data,
            assignation_file=assignation_file,
            preuve_signification_file=preuve_signification_file,
        )
    else:
        data = RequeteAssignationCreate(
            nom_huissier=nom_huissier,
            date_signification=date_signification_dt,
            date_audience=date_audience_dt,
        )
        create_requete_assignation_service(
            db=db,
            dossier_id=dossier_id,
            avocat_nom=user.nom,
            data=data,
            assignation_file=assignation_file,
            preuve_signification_file=preuve_signification_file,
        )

    return RedirectResponse(
        url=f"/dossiers/?requete_assignation_success=1",
        status_code=303,
    )
