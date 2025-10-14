import json
import os
import csv
from datetime import datetime
from typing import List, Union
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, Request, UploadFile, Query, Form, File
from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, FileResponse, HTMLResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.core.auth import get_current_avocat_or_clerk, get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.clients import get_all_clients, search_clients
from app.repositories.dossier import get_dossier_by_id, create_dossier_with_files
from app.repositories.facture import get_factures_by_dossier
from app.schemas.dossier import DossierCreate
from app.services.action_log import log_action_service
from app.services.dossier import (
    create_new_dossier_with_files,
    get_dossiers_by_user_service,
    get_dossier_by_id_service,
    update_dossier_with_files_service,
    get_dossiers_archiver_by_user_service,
    get_all_dossiers_by_user_service,
    get_all_dossiers_archiver_by_user_service,
    prepare_dossiers_for_export
)
from app.services.param_general import get_param_ordered, to_dict_list

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dossiers")
def list_dossiers(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    result = get_dossiers_by_user_service(db, user, page, per_page)

    log_action_service(db, user.id, "Consultation Dossier", f"Affichage liste dossier page {page}", dossier_id=None)

    return templates.TemplateResponse("dossier/list_dossier.html", {
        "request": request,
        "user": user,
        "dossiers": result["dossiers"],
        "pagination": {
            "page": result["page"],
            "per_page": result["per_page"],
            "total": result["total"],
            "total_pages": result["total_pages"]
        },
        "date_now": datetime.utcnow().date()
    })


@router.get("/dossiers_archiver")
def list_dossiers_archiver(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    result = get_dossiers_archiver_by_user_service(db, user, page, per_page)

    return templates.TemplateResponse("dossier/list_dossier_archiver.html", {
        "request": request,
        "user": user,
        "dossiers": result["dossiers"],
        "pagination": {
            "page": result["page"],
            "per_page": result["per_page"],
            "total": result["total"],
            "total_pages": result["total_pages"]
        }
    })


@router.get("/dossiers/export/csv")
def export_dossiers_csv(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    dossiers = get_all_dossiers_by_user_service(db, user)
    export_data = prepare_dossiers_for_export(dossiers)

    output = StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=dossiers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/dossiers_archiver/export/csv")
def export_dossiers_archiver_csv(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    dossiers = get_all_dossiers_archiver_by_user_service(db, user)
    export_data = prepare_dossiers_for_export(dossiers)

    output = StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=dossiers_archiver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/dossiers/export/pdf")
def export_dossiers_pdf(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    dossiers = get_all_dossiers_by_user_service(db, user)
    export_data = prepare_dossiers_for_export(dossiers)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>Liste des Dossiers - {datetime.now().strftime('%d/%m/%Y')}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    if export_data:
        headers = list(export_data[0].keys())
        data = [headers] + [[str(row[h]) for h in headers] for row in export_data]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=dossiers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


@router.get("/dossiers_archiver/export/pdf")
def export_dossiers_archiver_pdf(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_or_clerk)
):
    """Export des dossiers archivés en PDF"""
    dossiers = get_all_dossiers_archiver_by_user_service(db, user)
    export_data = prepare_dossiers_for_export(dossiers)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>Liste des Dossiers Archivés - {datetime.now().strftime('%d/%m/%Y')}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    if export_data:
        headers = list(export_data[0].keys())
        data = [headers] + [[str(row[h]) for h in headers] for row in export_data]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=dossiers_archiver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


@router.get("/dossiers/nouveau")
def new_dossier_form(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    type_affaire = get_param_ordered(db, "type_affaire", "asc")
    urgences = get_param_ordered(db, "urgence", "asc")
    civil_types = get_param_ordered(db, "sous_type_civil", "asc")
    penal_types = get_param_ordered(db, "sous_type_penal", "asc")
    qualite_types = get_param_ordered(db, "qualite_type", "asc")
    role_types = get_param_ordered(db, "role_type", "asc")
    clients = get_all_clients(db, user.id)

    return templates.TemplateResponse("dossier/create_dossier.html", {
        "request": request,
        "user": user,
        "type_affaire": to_dict_list(type_affaire),
        "urgences": to_dict_list(urgences),
        "civil_types": to_dict_list(civil_types),
        "penal_types": to_dict_list(penal_types),
        "qualite_types": to_dict_list(qualite_types),
        "role_types": to_dict_list(role_types),
        "clients": clients
    })


@router.get("/api/clients/search")
def search_clients_api(
        q: str = Query(..., min_length=2),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    clients = search_clients(db, user.id, q)
    return JSONResponse([
        {
            "id": c.id,
            "nom": c.nom,
            "email": c.email,
            "telephone": c.telephone,
            "adresse": c.adresse
        }
        for c in clients
    ])


@router.post("/dossiers/nouveau")
async def create_dossier_endpoint(
        dossier_data: str = Form(...),
        files: List[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    avocat_nom = user.nom
    dossier_dict = json.loads(dossier_data)

    try:
        dossier_in = DossierCreate(**dossier_dict)
        dossier = create_new_dossier_with_files(db, dossier_in, avocat_nom, files, user.id)
        return {"redirect_url": "/dossiers?success=1"}
    except Exception as e:
        db.rollback()
        print(f"Erreur création dossier: {e}")
        return {"redirect_url": "/dossiers/nouveau?error=1"}


@router.post("/dossiers/seed")
async def seed_dossiers_endpoint(
        dossiers_data: str = Form(...),
        avocat_id: int = Form(...),
        db: Session = Depends(get_db)
):

    avocat = db.query(User).filter(User.id == avocat_id, User.role == "avocat").first()
    if not avocat:
        raise HTTPException(status_code=404, detail="Avocat non trouvé")

    dossiers_list = json.loads(dossiers_data)
    created_count = 0
    errors = []

    for dossier_dict in dossiers_list:
        try:
            dossier_in = DossierCreate(**dossier_dict)
            dossier = create_dossier_with_files(
                db,
                dossier_in,
                avocat.nom,
                [],
                avocat.id
            )
            created_count += 1
        except Exception as e:
            errors.append(str(e))

    return {
        "created": created_count,
        "errors": len(errors),
        "error_details": errors[:10]
    }


@router.get("/dossiers/{dossier_id}", response_class=HTMLResponse)
def voir_dossier(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(get_current_avocat_or_clerk)
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    return templates.TemplateResponse("dossier/detail_dossier.html", {
        "request": request,
        "dossier": dossier,
        "user": user,
        "date_now": datetime.utcnow().date()
    })


@router.get("/dossiers/{dossier_id}/modifier", response_class=HTMLResponse)
def edit_dossier(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(get_current_avocat_user)
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    return templates.TemplateResponse("dossier/modifier_dossier.html", {
        "request": request,
        "dossier": dossier,
        "user": user
    })


@router.post("/dossiers/{dossier_id}/modifier")
async def update_dossier(
        dossier_id: int,
        nom_dossier: str = Form(...),
        consentement_rgpd: str = Form("false"),
        commentaire: str = Form(None),
        pieces_jointes: Union[List[UploadFile], UploadFile, None] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    consentement = consentement_rgpd.lower() == "true"

    if pieces_jointes is None:
        files = []
    elif isinstance(pieces_jointes, list):
        files = pieces_jointes
    else:
        files = [pieces_jointes]

    update_dossier_with_files_service(db, dossier_id, user.nom, nom_dossier, commentaire, consentement, files, user.id)
    return RedirectResponse(url=f"/dossiers/{dossier_id}", status_code=303)


@router.get("/documents/{filepath:path}", name="documents")
def documents(filepath: str):
    base_dir = os.path.abspath("app/documents")
    full_path = os.path.join(base_dir, filepath)

    if not os.path.commonpath([base_dir, os.path.abspath(full_path)]) == base_dir:
        return {"error": "Accès interdit"}

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path, filename=os.path.basename(full_path))
    return {"error": "Fichier non trouvé"}


@router.get("/dossiers/{dossier_id}/facture_dossier")
async def afficher_dossier(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    factures = get_factures_by_dossier(db, dossier_id)

    return templates.TemplateResponse("dossier/detail_facture.html", {
        "request": request,
        "dossier": dossier,
        "factures": factures,
        "user": user
    })