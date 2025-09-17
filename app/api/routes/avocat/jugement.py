from typing import Optional, List
from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user, get_current_user
from app.core.workflow_enums import ProcessStage
from app.db.session import get_db
from app.models.user import User
from app.schemas.jugement import JugementCreate, JugementUpdate
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.email import send_email, send_jugement_favorable_email
from app.services.jugement_service import (
    create_jugement_service,
    update_jugement_service,
    get_jugement_by_dossier_service,
    archiver_jugement, get_jugement_by_id_service, enregistrer_grosse_service, create_jugement_defavorable_service,
)
from app.services.param_general import get_param_ordered, to_dict_list
from app.services.workflow_guard import WorkflowGuard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers/{dossier_id}/jugement_favorable", response_class=HTMLResponse)
def jugement_favorable_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = get_jugement_by_dossier_service(db, dossier_id)
    return templates.TemplateResponse(
        "avocat/jugement/jugement_favorable_form.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement},
    )


@router.post("/dossiers/{dossier_id}/jugement_favorable")
async def create_jugement_favorable(
        dossier_id: int,
        date_jugement: str = Form(...),
        texte_decision: Optional[str] = Form(None),
        delai_appel: Optional[int] = Form(None),
        execution_provisoire: Optional[bool] = Form(False),
        jugement_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),
):
    data = JugementCreate(
        dossier_id=dossier_id,
        date_jugement=date_jugement,
        texte_decision=texte_decision,
        delai_appel=delai_appel,
        execution_provisoire=execution_provisoire,
    )
    try:
        create_jugement_service(
            db=db,
            dossier_id=dossier_id,
            avocat_nom=user.nom,
            data=data,
            user_id=user1.id,
            jugement_file=jugement_file
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/jugement_notification", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement_notification", response_class=HTMLResponse)
def jugement_notification_form(
        dossier_id: int,
        request: Request,
        user: User = Depends(get_current_avocat_user),
):
    return templates.TemplateResponse(
        "avocat/jugement/jugement_notification.html",
        {"request": request, "user": user, "dossier_id": dossier_id},
    )


@router.post("/dossiers/{dossier_id}/jugement_notification")
async def send_jugement_notification(
        dossier_id: int,
        notify_email: Optional[bool] = Form(False),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    WorkflowGuard.advance(dossier, ProcessStage.NOTIFICATION_CLIENT, db)
    for demandeur in dossier.client.demandeurs:
        if demandeur.email:
            await send_jugement_favorable_email(demandeur.email, dossier)
    print(f"Notification envoyée - Email: {notify_email}")

    return RedirectResponse(
        url=f"/dossiers", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement_rappel", response_class=HTMLResponse)
def jugement_rappel_form(
        dossier_id: int,
        request: Request,
        user: User = Depends(get_current_avocat_user),
):
    return templates.TemplateResponse(
        "avocat/jugement/jugement_rappel.html",
        {"request": request, "user": user, "dossier_id": dossier_id},
    )


@router.post("/dossiers/{dossier_id}/jugement_rappel")
async def send_jugement_rappel(
        dossier_id: int,
        rappel_email: Optional[bool] = Form(False),
        rappel_whatsapp: Optional[bool] = Form(False),
        user: User = Depends(get_current_avocat_user),
):
    print(f"Rappel envoyé - Email: {rappel_email}, WhatsApp: {rappel_whatsapp}")

    return RedirectResponse(
        url=f"/dossiers/{dossier_id}/jugement_archiver", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement_archiver", response_class=HTMLResponse)
def archiver_form(
        dossier_id: int,
        request: Request,
        user: User = Depends(get_current_avocat_user),
):
    return templates.TemplateResponse(
        "avocat/jugement/jugement_archiver.html",
        {"request": request, "user": user, "dossier_id": dossier_id},
    )


@router.post("/dossiers/{dossier_id}/jugement_archiver")
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


@router.get("/dossiers/{dossier_id}/jugement_update/{jugement_id}", response_class=HTMLResponse)
def update_jugement_form(
        dossier_id: int,
        jugement_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = get_jugement_by_id_service(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    return templates.TemplateResponse(
        "avocat/jugement/jugement_update_form.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement},
    )


@router.post("/dossiers/{dossier_id}/jugement_update/{jugement_id}")
async def update_jugement_route(
        dossier_id: int,
        jugement_id: int,
        texte_decision: Optional[str] = Form(None),
        delai_appel: Optional[int] = Form(None),
        execution_provisoire: Optional[bool] = Form(False),
        statut: Optional[str] = Form(None),
        jugement_file: Optional[UploadFile] = File(None),
        scans_grosse: Optional[List[UploadFile]] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),
):
    data = JugementUpdate(
        texte_decision=texte_decision,
        delai_appel=delai_appel,
        execution_provisoire=execution_provisoire,
        statut=statut
    )
    try:
        update_jugement_service(
            db=db,
            jugement_id=jugement_id,
            avocat_nom=user.nom,
            data=data,
            user_id=user1.id,
            jugement_file=jugement_file,
            scan_grosse=scans_grosse
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(
        url=f"/dossiers?update_jugement_success=1", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement/{jugement_id}/enregistrer_grosse", response_class=HTMLResponse)
def enregistrer_grosse_form(
        dossier_id: int,
        jugement_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = get_jugement_by_id_service(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement introuvable")

    return templates.TemplateResponse(
        "avocat/jugement/enregistrer_grosse_form.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement},
    )


@router.post("/dossiers/{dossier_id}/jugement/{jugement_id}/enregistrer_grosse")
async def enregistrer_grosse_route(
        dossier_id: int,
        jugement_id: int,
        scans_grosse: List[UploadFile] = File(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),
):
    try:
        enregistrer_grosse_service(
            db=db,
            jugement_id=jugement_id,
            avocat_nom=user.nom,
            scan_grosse=scans_grosse,
            user_id=user1.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(
        url=f"/dossiers/?grosse_saved=1", status_code=303
    )


@router.get("/dossiers/{dossier_id}/jugement_defavorable", response_class=HTMLResponse)
def jugement_defavorable_form(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
):
    jugement = get_jugement_by_dossier_service(db, dossier_id)
    sous_type = get_param_ordered(db, "sous_type_jugement_defavorable", "asc")
    return templates.TemplateResponse(
        "avocat/jugement/jugement_defavorable_form.html",
        {"request": request, "user": user, "dossier_id": dossier_id, "jugement": jugement,
         "sous_type": to_dict_list(sous_type), }
    )


@router.post("/dossiers/{dossier_id}/jugement_defavorable")
async def create_jugement_defavorable(
        dossier_id: int,
        date_jugement: str = Form(...),
        texte_decision: Optional[str] = Form(None),
        sous_type: str = Form(...),
        delai_appel: Optional[int] = Form(None),
        execution_provisoire: Optional[bool] = Form(False),
        jugement_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        user1: User = Depends(get_current_user),

):
    data = JugementCreate(
        dossier_id=dossier_id,
        sous_type=sous_type,
        date_jugement=date_jugement,
        texte_decision=texte_decision,
        delai_appel=delai_appel,
        execution_provisoire=execution_provisoire,
    )
    try:
        create_jugement_defavorable_service(
            db=db,
            dossier_id=dossier_id,
            avocat_nom=user.nom,
            data=data,
            user_id=user1.id,
            jugement_file=jugement_file
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if sous_type == "contradictoire":
        return RedirectResponse(
            url=f"/dossiers/{dossier_id}/archiver", status_code=303
        )
    else:
        return RedirectResponse(
            url=f"/dossiers", status_code=303
        )


@router.post("/dossiers/{dossier_id}/jugement_contradictoire")
def choix_contradictoire(dossier_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_avocat_user)
                         ):
    dossier = get_dossier_by_id_service(db, dossier_id)
    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_CONTRADICTOIRE, db)
    log_action_service(db, user.id, "Création jugement contradictoire",
                       f"Création du jugement contradictoire pour le dossier {dossier.numero_dossier}",
                       dossier.id)
    return RedirectResponse(url=f"/dossiers", status_code=303)


@router.post("/dossiers/{dossier_id}/jugement_par_defaut")
def choix_par_defaut(dossier_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_avocat_user)):
    dossier = get_dossier_by_id_service(db, dossier_id)
    WorkflowGuard.advance(dossier, ProcessStage.PAR_DEFAUT, db)
    log_action_service(db, user.id, "Création jugement par defaut",
                       f"Création du jugement par defaut pour le dossier {dossier.numero_dossier}",
                       dossier.id)
    return RedirectResponse(url=f"/dossiers", status_code=303)
