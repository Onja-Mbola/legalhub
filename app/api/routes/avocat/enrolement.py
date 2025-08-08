from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.enrolement import get_enrolement_by_dossier_service, insert_enrolement_with_file

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/enrolement", response_class=templates.TemplateResponse)
async def enrolement_form(
    dossier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user),
):
    enrolement = get_enrolement_by_dossier_service(db, dossier_id)
    if not enrolement:
        enrolement = None
    return templates.TemplateResponse("avocat/enrolement/form.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "enrolement": enrolement
    })

@router.post("/dossiers/{dossier_id}/enrolement")
async def create_or_update_enrolement(
    dossier_id: int,
    numero_role: str = Form(...),
    date_enrolement: str = Form(...),
    frais_payes: Optional[float] = Form(None),
    greffier: Optional[str] = Form(None),
    preuve_enrolement: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_avocat_user)
):
    try:
        insert_enrolement_with_file(
            db=db,
            dossier_id=dossier_id,
            avocat_nom=user.nom,
            numero_role=numero_role,
            date_enrolement_str=date_enrolement,
            frais_payes=frais_payes,
            greffier=greffier,
            preuve_enrolement_file=preuve_enrolement
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(url="/dossiers?enrolement_success=1", status_code=303)



