from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query, HTTPException, Form
from fastapi.responses import StreamingResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.services.action_log import log_action_service
from app.services.client_service import (
    get_clients_list_service,
    get_client_detail_service,
    export_clients_csv,
    get_clients_export_data
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

from app.services.param_general import get_param_ordered, to_dict_list

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/clients")
def list_clients(
        request: Request,
        page: int = Query(1, ge=1),
        search: Optional[str] = Query(None),
        sort_by: str = Query("nom", regex="^(nom|dossiers)$"),
        order: str = Query("asc", regex="^(asc|desc)$"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    result = get_clients_list_service(
        db, user.id, page, 20, search, sort_by, order
    )

    log_action_service(
        db, user.id, "Consultation Clients",
        "Affichage liste clients", None
    )

    return templates.TemplateResponse("avocat/client/list_clients.html", {
        "request": request,
        "user": user,
        "clients": result["clients"],
        "pagination": result["pagination"],
        "search": search or "",
        "sort_by": sort_by,
        "order": order
    })


@router.get("/clients/nouveau")
def create_client_form(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    log_action_service(
        db, user.id, "Accès formulaire création client",
        "Affichage formulaire nouveau client", None
    )

    qualite_types = get_param_ordered(db, "qualite_type", "asc")


    return templates.TemplateResponse("avocat/client/create_client.html", {
        "request": request,
        "user": user,
        "error_msg": None,
        "qualite_types": to_dict_list(qualite_types),

    })


@router.post("/clients/nouveau")
def create_client_submit(
        request: Request,
        nom: str = Form(...),
        email: Optional[str] = Form(None),
        telephone: Optional[str] = Form(None),
        adresse: Optional[str] = Form(None),
        qualite: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:
        if not nom or nom.strip() == "":
            raise HTTPException(status_code=400, detail="Le nom du client est obligatoire")

        new_client = Client(
            nom=nom.strip(),
            email=email.strip() if email else None,
            telephone=telephone.strip() if telephone else None,
            adresse=adresse.strip() if adresse else None,
            qualite=qualite if qualite else None,
            avocat_id=user.id
        )

        db.add(new_client)
        db.commit()
        db.refresh(new_client)

        log_action_service(
            db, user.id, "Création Client",
            f"Nouveau client créé : {new_client.nom} (ID: {new_client.id})", None
        )

        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=f"/clients/{new_client.id}",
            status_code=303
        )

    except Exception as e:
        db.rollback()
        error_msg = f"Erreur lors de la création du client : {str(e)}"

        return templates.TemplateResponse("avocat/client/create_client.html", {
            "request": request,
            "user": user,
            "error_msg": error_msg,
            "nom": nom,
            "email": email,
            "telephone": telephone,
            "adresse": adresse,
            "qualite": qualite
        })


@router.get("/clients/{client_id}/modifier")
def update_client_form(
        client_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    """Affiche le formulaire de modification d'un client"""

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    log_action_service(
        db, user.id, "Accès formulaire modification client",
        f"Affichage formulaire modification client {client_id}", None
    )

    return templates.TemplateResponse("avocat/client/update_client.html", {
        "request": request,
        "user": user,
        "client": client,
        "error_msg": None
    })


@router.post("/clients/{client_id}/modifier")
def update_client_submit(
        client_id: int,
        request: Request,
        nom: str = Form(...),
        email: Optional[str] = Form(None),
        telephone: Optional[str] = Form(None),
        adresse: Optional[str] = Form(None),
        qualite: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        if not nom or nom.strip() == "":
            raise HTTPException(status_code=400, detail="Le nom du client est obligatoire")

        client.nom = nom.strip()
        client.email = email.strip() if email else None
        client.telephone = telephone.strip() if telephone else None
        client.adresse = adresse.strip() if adresse else None
        client.qualite = qualite if qualite else None

        db.commit()
        db.refresh(client)

        log_action_service(
            db, user.id, "Modification Client",
            f"Client modifié: {client.nom} (ID: {client.id})", None
        )

        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=f"/clients/{client.id}",
            status_code=303
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = f"Erreur lors de la modification du client: {str(e)}"

        client = db.query(Client).filter(Client.id == client_id).first()

        return templates.TemplateResponse("avocat/client/update_client.html", {
            "request": request,
            "user": user,
            "client": client,
            "error_msg": error_msg
        })


@router.post("/clients/{client_id}/supprimer")
def delete_client(
        client_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    try:
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        if client.dossiers and len(client.dossiers) > 0:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer ce client car il est associé à des dossiers"
            )

        client_nom = client.nom

        db.delete(client)
        db.commit()

        log_action_service(
            db, user.id, "Suppression Client",
            f"Client supprimé: {client_nom} (ID: {client_id})", None
        )

        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url="/clients?success=Client supprimé avec succès",
            status_code=303
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")


@router.get("/clients/{client_id}")
def detail_client(
        client_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    client_data = get_client_detail_service(db, client_id, user.id)

    if not client_data:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    log_action_service(
        db, user.id, "Consultation Client",
        f"Affichage détail client {client_id}", None
    )

    return templates.TemplateResponse("avocat/client/detail_client.html", {
        "request": request,
        "user": user,
        "client": client_data["client"],
        "stats": client_data["stats"],
        "demandeurs": client_data["demandeurs"],
        "dossiers": client_data["dossiers"],
        "date_now": datetime.utcnow().date()
    })


@router.get("/clients/export/csv")
def export_clients_csv_route(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    csv_data = export_clients_csv(db, user.id)

    log_action_service(
        db, user.id, "Export Clients",
        "Export CSV liste clients", None
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/clients/export/pdf")
def export_clients_pdf_route(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    clients_data = get_clients_export_data(db, user.id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5 * cm)

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    elements.append(Paragraph(f"Liste des Clients - {user.nom}", title_style))
    elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [['ID', 'Nom', 'Email', 'Téléphone', 'Rôle', 'Dossiers', 'Statut']]

    for client in clients_data:
        statut_label = {
            "gros_client": "Gros client",
            "client_regulier": "Régulier",
            "nouveau_client": "Nouveau"
        }.get(client["statut"], "")

        data.append([
            str(client["id"]),
            client["nom"][:30],
            client["email"][:30] if client["email"] != "N/A" else "N/A",
            client["telephone"] or "N/A",
            client["type"][:20] if client["type"] != "N/A" else "N/A",
            str(client["total_dossiers"]),
            statut_label
        ])

    table = Table(data, colWidths=[2 * cm, 5 * cm, 5 * cm, 3.5 * cm, 4 * cm, 2.5 * cm, 3 * cm])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    log_action_service(
        db, user.id, "Export Clients",
        "Export PDF liste clients", None
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )
