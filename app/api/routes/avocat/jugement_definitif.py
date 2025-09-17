from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user, get_current_user
from app.core.workflow_enums import ProcessStage
from app.db.session import get_db
from app.models.user import User
from app.schemas.jugement_definitif import JugementDefinitifCreate, JugementDefinitifUpdate
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.email import send_jugement_favorable_email, send_jugement_definitif_email
from app.services.jugement_definitif_service import (
    create_jugement_definitif_service,
    update_jugement_definitif_service,
    get_jugement_definitif_by_id_service,
    get_jugements_definitifs_by_dossier_service
)
from app.services.jugement_service import get_jugement_by_dossier_service, archiver_jugement
from app.services.workflow_guard import WorkflowGuard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/jugement_definitif/{deliberation_id}", response_class=HTMLResponse)
def jugement_definitif_form(
        dossier_id: int,
        deliberation_id: int,
        request: Request,
        jugement_id: Optional[int] = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = None
    if jugement_id:
        jugement = get_jugement_definitif_by_id_service(db, jugement_id)
        if not jugement:
            raise HTTPException(status_code=404, detail="Jugement définitif introuvable")
    else:
        jugements = get_jugements_definitifs_by_dossier_service(db, dossier_id)
        if jugements:
            jugement = jugements[0]

    return templates.TemplateResponse(
        "avocat/jugements_definitifs/form.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement,
         "deliberation_id": deliberation_id},
    )


@router.get("/dossiers/{dossier_id}/jugement_def/{jugement_id}/update", response_class=HTMLResponse)
def jugement_definitif_form(
        dossier_id: int,
        jugement_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = None
    if jugement_id:
        jugement = get_jugement_definitif_by_id_service(db, jugement_id)
        if not jugement:
            raise HTTPException(status_code=404, detail="Jugement définitif introuvable")
    else:
        jugements = get_jugements_definitifs_by_dossier_service(db, dossier_id)
        if jugements:
            jugement = jugements[0]

    return templates.TemplateResponse(
        "avocat/jugements_definitifs/form_update.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement},
    )


@router.post("/dossiers/{dossier_id}/jugement_definitif")
async def save_jugement_definitif(
        dossier_id: int,
        jugement_id: Optional[int] = Form(None),
        deliberation_id: Optional[int] = Form(None),
        date_jugement: str = Form(...),
        texte_jugement: Optional[str] = Form(None),
        observations: Optional[str] = Form(None),
        fichiers: Optional[List[UploadFile]] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),
):
    if jugement_id:
        data = JugementDefinitifUpdate(
            texte_jugement=texte_jugement,
            observations=observations
        )
        try:
            update_jugement_definitif_service(
                db=db,
                jugement_id=int(jugement_id),
                avocat_nom=user.nom,
                user_id=user1.id,
                data=data,
                fichiers=fichiers
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        redirect_url = f"/dossiers?jugement_definitif_update_success=1"
    else:
        data = JugementDefinitifCreate(
            dossier_id=dossier_id,
            deliberation_id=deliberation_id,
            date_jugement=datetime.strptime(date_jugement, "%Y-%m-%d").date(),
            texte_jugement=texte_jugement,
            observations=observations
        )
        try:
            create_jugement_definitif_service(
                db=db,
                dossier_id=dossier_id,
                avocat_nom=user.nom,
                data=data,
                user_id=user1.id,
                fichiers=fichiers
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        redirect_url = f"/dossiers?jugement_definitif_create_success=1"

    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/dossiers/{dossier_id}/jugement_definitif_notification", response_class=HTMLResponse)
def jugement_notification_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    return templates.TemplateResponse(
        "avocat/jugements_definitifs/jugement_definitf_notification.html",
        {"request": request, "user": user, "dossier": dossier},
    )


@router.post("/dossiers/{dossier_id}/jugement_definitif_notification")
async def send_jugement_notification(
        dossier_id: int,
        notify_email: Optional[bool] = Form(False),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if not dossier.jugements_definitifs:
        raise HTTPException(status_code=400, detail="Aucun jugement définitif enregistré pour ce dossier")

    if dossier.current_stage != ProcessStage.JUGEMENT_DEFINITIF.value:
        raise HTTPException(
            status_code=400,
            detail="Le dossier n'est pas à l'étape de jugement définitif, notification impossible."
        )

    WorkflowGuard.advance(dossier, ProcessStage.NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT, db)

    for demandeur in dossier.client.demandeurs:
        if demandeur.email:
            await send_jugement_definitif_email(demandeur.email, dossier)

    print(f"Notification envoyée - Email: {notify_email}")

    log_action_service(db, user.id, "Envoi Mail jugement définitif",
                       f"Envoi Mail du jugement définitif pour le dossier {dossier.numero_dossier}",
                       dossier.id)

    return RedirectResponse(
        url=f"/dossiers", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement_definitif_archiver", response_class=HTMLResponse)
def archiver_form(
        dossier_id: int,
        request: Request,
        user: User = Depends(get_current_avocat_user),
):
    return templates.TemplateResponse(
        "avocat/jugements_definitifs/jugement_definitif_archiver.html",
        {"request": request, "user": user, "dossier_id": dossier_id},
    )


@router.post("/dossiers/{dossier_id}/jugement_definitif_archiver")
async def archiver_jugement_route(
        dossier_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),
):
    try:
        jugements = get_jugement_by_dossier_service(db, dossier_id)
        if not jugements:
            raise HTTPException(status_code=404, detail="Aucun jugement trouvé")
        jugement = jugements[0]
        archiver_jugement(db, jugement.id, user1.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(url="/dossiers?archivage_success=1", status_code=303)
