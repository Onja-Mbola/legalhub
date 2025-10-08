from typing import Optional

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.enrolement import get_enrolement_by_dossier_service, insert_enrolement_with_file, \
    get_enrolement_by_numero_role_service, insert_enrolement_appel_with_file
from app.services.jugement_service import get_jugement_by_id_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/enrolement", response_class=HTMLResponse)
def enrolement_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=False)
    if not enrolement or enrolement.jugement_id is not None:
        enrolement = None
    return templates.TemplateResponse("avocat/enrolement/form.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "enrolement": enrolement
    })


@router.post("/dossiers/{dossier_id}/enrolement")
async def create_or_update_enrolement(
        request: Request,
        dossier_id: int,
        numero_role: str = Form(...),
        date_enrolement: str = Form(...),
        frais_payes: float = Form(None),
        greffier: str = Form(None),
        preuve_enrolement: UploadFile = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    existing = get_enrolement_by_numero_role_service(db, numero_role)
    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=False)

    if existing and existing.dossier_id != dossier_id:
        return templates.TemplateResponse("avocat/enrolement/form.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement": enrolement,
            "error_msg": f"Le numéro de rôle '{numero_role}' existe déjà pour un autre dossier. Il doit être unique."
        })

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
        return templates.TemplateResponse("avocat/enrolement/form.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement": get_enrolement_by_dossier_service(db, dossier_id, with_jugement=False),
            "error_msg": str(e)
        })

    return RedirectResponse(url="/dossiers?enrolement_success=1", status_code=303)


@router.get("/dossiers/{dossier_id}/enrolement_appel/{jugement_id}", response_class=HTMLResponse)
def enrolement_form_appel(
        dossier_id: int,
        jugement_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)
    if not enrolement or not getattr(enrolement, "jugement_id", None):
        enrolement = None

    jugement = get_jugement_by_id_service(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    return templates.TemplateResponse("avocat/enrolement/form_appel.html", {
        "request": request,
        "user": user,
        "dossier_id": dossier_id,
        "enrolement": enrolement,
        "jugement": jugement
    })


@router.post("/dossiers/{dossier_id}/enrolement_appel/{jugement_id}")
async def create_or_update_enrolement_appel(
        request: Request,
        dossier_id: int,
        jugement_id: int,
        numero_role: str = Form(...),
        date_enrolement: str = Form(...),
        frais_payes: float = Form(None),
        greffier: str = Form(None),
        preuve_enrolement: UploadFile = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    existing = get_enrolement_by_numero_role_service(db, numero_role)
    enrolement = get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True)
    if not enrolement or not getattr(enrolement, "jugement_id", None):
        enrolement = None
    jugement = get_jugement_by_id_service(db, jugement_id)

    if existing and existing.dossier_id != dossier_id:
        return templates.TemplateResponse("avocat/enrolement/form_appel.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "enrolement": enrolement,
            "jugement": jugement,
            "error_msg": f"Le numéro de rôle '{numero_role}' existe déjà pour un autre dossier. Il doit être unique."
        })

    try:
        insert_enrolement_appel_with_file(
            db=db,
            dossier_id=dossier_id,
            jugement_id=jugement.id,
            avocat_nom=user.nom,
            numero_role=numero_role,
            date_enrolement_str=date_enrolement,
            frais_payes=frais_payes,
            greffier=greffier,
            preuve_enrolement_file=preuve_enrolement
        )
    except Exception as e:
        return templates.TemplateResponse("avocat/enrolement/form_appel.html", {
            "request": request,
            "user": user,
            "dossier_id": dossier_id,
            "jugement": get_jugement_by_id_service(db, jugement_id),
            "enrolement": get_enrolement_by_dossier_service(db, dossier_id, with_jugement=True),
            "error_msg": str(e)
        })

    return RedirectResponse(url="/dossiers?enrolement_appel_success=1", status_code=303)
