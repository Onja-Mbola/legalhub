import os
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi import Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.facture import StatutFacture, TypeRappel, Facture
from app.models.user import User
from app.repositories import facture as facture_repo
from app.repositories.dossier import get_dossiers_by_avocat
from app.repositories.facture import get_facture_by_id
from app.repositories.paiement import PaiementRepository
from app.schemas.facture import FactureCreate, FactureUpdate
from app.services import facture_service
from app.services.paiement_service import add_paiement_service, get_paiements_by_facture_service, \
    update_paiement_service, delete_paiement_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/factures", response_class=HTMLResponse)
def list_factures(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        page: int = Query(1, ge=1),
        statut: Optional[str] = Query(None),
        search: Optional[str] = Query(None)
):
    limit = 20
    offset = (page - 1) * limit

    factures = facture_repo.get_factures_by_avocat(db, user.id, offset, limit)

    if statut and statut in [s.value for s in StatutFacture]:
        factures = [f for f in factures if f.statut.value == statut]
    if search:
        search_lower = search.lower()
        factures = [
            f for f in factures
            if search_lower in f.nom_client_anonyme.lower() or search_lower in f.numero_facture.lower()
        ]
    stats = facture_service.get_facture_statistics(db, user.id)

    return templates.TemplateResponse("avocat/facture/liste_facture.html", {
        "request": request,
        "user": user,
        "factures": factures,
        "current_page": page,
        "statut_filter": statut,
        "search_filter": search,
        "stats": stats,
        "StatutFacture": StatutFacture
    })


@router.get("/factures/nouveau", response_class=HTMLResponse)
def new_facture_form(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user),
        dossier_id: Optional[int] = Query(None)
):
    dossiers = get_dossiers_by_avocat(db, user.id)

    return templates.TemplateResponse("avocat/facture/form_facture.html", {
        "request": request,
        "user": user,
        "dossiers": dossiers,
        "selected_dossier_id": dossier_id,
        "TypeRappel": TypeRappel,
        "facture": None
    })


@router.post("/factures/nouveau")
async def create_facture(
        request: Request,
        dossier_id: int = Form(...),
        nom_client_anonyme: str = Form(...),
        description: str = Form(...),
        montant_ht: float = Form(...),
        taux_tva: float = Form(20.0),
        date_echeance: date = Form(...),
        rappel_active: bool = Form(False),
        type_rappel: TypeRappel = Form(TypeRappel.AUCUN),
        notes_internes: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:
        facture_data = FactureCreate(
            dossier_id=dossier_id,
            nom_client_anonyme=nom_client_anonyme,
            description=description,
            montant_ht=montant_ht,
            taux_tva=taux_tva,
            date_echeance=date_echeance,
            rappel_active=rappel_active,
            type_rappel=type_rappel,
            notes_internes=notes_internes
        )

        facture = facture_service.create_facture_with_file(
            db, facture_data, user.id, user.nom
        )

        return RedirectResponse(
            url=f"/factures/{facture.id}?success=1",
            status_code=303
        )

    except Exception as e:
        dossiers = get_dossiers_by_avocat(db, user.id)
        return templates.TemplateResponse("avocat/facture/form_facture.html", {
            "request": request,
            "user": user,
            "dossiers": dossiers,
            "TypeRappel": TypeRappel,
            "facture": None,
            "error_msg": str(e)
        })


@router.get("/factures/{facture_id}", response_class=HTMLResponse)
def view_facture(
        facture_id: int,
        request: Request,
        success: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    paiements = get_paiements_by_facture_service(db, facture_id)
    today = datetime.utcnow().date()
    facture.date_creation_plus3h = facture.date_creation + timedelta(hours=3)
    facture.date_emission_plus3h = facture.date_emission + timedelta(hours=3)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    return templates.TemplateResponse("avocat/facture/detail_facture.html", {
        "request": request,
        "user": user,
        "facture": facture,
        "StatutFacture": StatutFacture,
        "success": success,
        "today": today,
        "paiements": paiements
    })


@router.get("/factures/{facture_id}/modifier", response_class=HTMLResponse)
def edit_facture_form(
        facture_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    dossiers = get_dossiers_by_avocat(db, user.id)

    return templates.TemplateResponse("avocat/facture/form_facture.html", {
        "request": request,
        "user": user,
        "dossiers": dossiers,
        "facture": facture,
        "TypeRappel": TypeRappel,
        "StatutFacture": StatutFacture
    })


@router.post("/factures/{facture_id}/modifier")
async def update_facture(
        facture_id: int,
        request: Request,
        nom_client_anonyme: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        montant_ht: Optional[float] = Form(None),
        taux_tva: Optional[float] = Form(None),
        date_echeance: Optional[date] = Form(None),
        statut: Optional[StatutFacture] = Form(None),
        rappel_active: Optional[bool] = Form(None),
        type_rappel: Optional[TypeRappel] = Form(None),
        notes_internes: Optional[str] = Form(None),
        preuve_paiement: UploadFile = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:

        facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
        if not facture:
            raise HTTPException(status_code=404, detail="Facture non trouvée")

        if facture.statut == StatutFacture.PAYEE and montant_ht is not None:
            raise HTTPException(
                status_code=400,
                detail="Impossible de modifier le montant d'une facture déjà payée."
            )

        facture_update = FactureUpdate(
            nom_client_anonyme=nom_client_anonyme,
            description=description,
            montant_ht=montant_ht,
            taux_tva=taux_tva,
            date_echeance=date_echeance,
            statut=statut,
            rappel_active=rappel_active,
            type_rappel=type_rappel,
            notes_internes=notes_internes
        )

        facture = facture_service.update_facture_with_files(
            db, facture_id, facture_update, user.id, user.nom, preuve_paiement
        )

        return RedirectResponse(
            url=f"/factures/{facture_id}?success=1",
            status_code=303
        )

    except Exception as e:
        facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
        dossiers = get_dossiers_by_avocat(db, user.id)

        return templates.TemplateResponse("avocat/facture/form_facture.html", {
            "request": request,
            "user": user,
            "dossiers": dossiers,
            "facture": facture,
            "TypeRappel": TypeRappel,
            "StatutFacture": StatutFacture,
            "error_msg": str(e)
        })


@router.post("/factures/{facture_id}/envoyer")
async def send_facture_email_route(
        facture_id: int,
        request: Request,
        email_client: str = Form(...),
        message_personnalise: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    try:
        facture_data = {
            'numero_facture': facture.numero_facture,
            'montant_ttc': facture.montant_ttc,
            'date_echeance': facture.date_echeance.isoformat(),
            'nom_client': facture.nom_client_anonyme,
            'description': facture.description,
            'message_personnalise': message_personnalise
        }

        facture_service.send_facture_email_task.delay(
            email_client, facture_data, facture.fichier_facture
        )

        if facture.statut == StatutFacture.BROUILLON:
            facture_update = FactureUpdate(
                statut=StatutFacture.ENVOYEE,
                date_emission=datetime.utcnow()
            )
            facture_service.update_facture_with_files(
                db, facture_id, facture_update, user.id, user.nom
            )

        return RedirectResponse(
            url=f"/factures/{facture_id}?email_sent=1",
            status_code=303
        )

    except Exception as e:
        return RedirectResponse(
            url=f"/factures/{facture_id}?error=email_failed",
            status_code=303
        )


@router.get("/factures/{facture_id}/download")
def download_facture(
        facture_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture or not facture.fichier_facture:
        raise HTTPException(status_code=404, detail="Fichier de facture non trouvé")

    if not os.path.exists(facture.fichier_facture):
        raise HTTPException(status_code=404, detail="Fichier physique non trouvé")

    return FileResponse(
        facture.fichier_facture,
        media_type='application/pdf',
        filename=f"facture_{facture.numero_facture}.pdf"
    )


@router.delete("/factures/{facture_id}")
def delete_facture_route(
        facture_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    success = facture_repo.delete_facture(db, facture_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    return {"message": "Facture supprimée avec succès"}


@router.get("/dossiers/{dossier_id}/factures", response_class=HTMLResponse)
def factures_dossier(
        dossier_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    factures = facture_repo.get_factures_by_dossier(db, dossier_id)

    return templates.TemplateResponse("avocat/facture/liste_facture.html", {
        "request": request,
        "user": user,
        "factures": factures,
        "dossier_id": dossier_id,
        "StatutFacture": StatutFacture
    })


# @router.get("/statistiques/facturation", response_class=HTMLResponse)
# def statistiques_facturation(
#         request: Request,
#         periode: str = Query("annee"),
#         db: Session = Depends(get_db),
#         user: User = Depends(get_current_avocat_user)
# ):
#     stats_facturation = facture_service.get_facture_statistics(db, user.id, "annee")
#     stats_revenus = facture_service.get_facture_statistics(db, user.id, "revenus")
#
#     return templates.TemplateResponse("avocat/facture/statistiques.html", {
#         "request": request,
#         "user": user,
#         "stats_facturation": stats_facturation,
#         "stats_revenus": stats_revenus,
#         "periode": periode
#     })

# @router.get("/statistiques/facturation", response_class=HTMLResponse)
# def statistiques_facturation(
#         request: Request,
#         periode: str = Query("annee"),
#         db: Session = Depends(get_db),
#         user: User = Depends(get_current_avocat_user)
# ):
#     stats_facturation = facture_service.get_facture_statistics(db, user.id, "annee")
#     stats_revenus = facture_service.get_facture_statistics(db, user.id, "revenus")
#
#     if stats_revenus is None:
#         from app.schemas.facture import StatistiqueRevenu
#         stats_revenus = StatistiqueRevenu(
#             revenus_par_mois={},
#             revenus_par_type_affaire={},
#             evolution_mensuelle={}
#         )
#
#     return templates.TemplateResponse("avocat/facture/statistiques.html", {
#         "request": request,
#         "user": user,
#         "stats_facturation": stats_facturation,
#         "stats_revenus": stats_revenus,
#         "periode": periode
#     })


@router.get("/statistiques/facturation", response_class=HTMLResponse)
def statistiques_facturation(
        request: Request,
        periode: str = Query("annee"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    try:
        stats_facturation = facture_service.get_facture_statistics(db, user.id, "annee")

        print("DEBUG stats_facturation:", stats_facturation)

        stats_revenus = facture_service.get_facture_statistics(db, user.id, "revenus")
        print("DEBUG stats_revenus:", stats_revenus)

        if stats_revenus is None:
            from app.schemas.facture import StatistiqueRevenu
            stats_revenus = StatistiqueRevenu(
                revenus_par_mois={},
                revenus_par_type_affaire={},
                evolution_mensuelle={}
            )

        factures_en_retard = []
        try:
            factures_en_retard = facture_repo.get_factures_en_retard(db, user.id)
            pass
        except Exception as e:
            print(f"Erreur récupération factures en retard: {e}")
            factures_en_retard = []

        top_clients = []
        try:
            top_clients = facture_repo.get_top_clients(db, user.id, limit=5)
            pass
        except Exception as e:
            print(f"Erreur récupération top clients: {e}")
            top_clients = []

        delai_paiement_moyen = "N/A"
        try:
            delai_paiement_moyen = facture_repo.get_delai_paiement_moyen(db, user.id)
            pass
        except Exception as e:
            print(f"Erreur calcul délai paiement: {e}")

        context = {
            "request": request,
            "user": user,
            "stats_facturation": stats_facturation,
            "stats_revenus": stats_revenus,
            "factures_en_retard": factures_en_retard,
            "top_clients": top_clients,
            "delai_paiement_moyen": delai_paiement_moyen,
            "periode": periode,
            "now": datetime.now
        }

        return templates.TemplateResponse("avocat/facture/statistiques.html", context)

    except Exception as e:
        print(f"Erreur dans statistiques_facturation: {e}")
        from app.schemas.facture import StatistiqueRevenu, StatistiqueFacturation

        default_stats_facturation = StatistiqueFacturation(
            total_facture=0,
            total_paye=0,
            total_impaye=0,
            nombre_factures_total=0,
            nombre_factures_payees=0,
            nombre_factures_impayees=0,
            taux_recouvrement=0
        )

        default_stats_revenus = StatistiqueRevenu(
            revenus_par_mois={},
            revenus_par_type_affaire={},
            evolution_mensuelle={}
        )

        context = {
            "request": request,
            "user": user,
            "stats_facturation": default_stats_facturation,
            "stats_revenus": default_stats_revenus,
            "factures_en_retard": [],
            "top_clients": [],
            "delai_paiement_moyen": "N/A",
            "periode": periode,
            "now": datetime.now,
            "error_message": "Erreur lors du chargement des statistiques"
        }


@router.get("/factures/{facture_id}/paiements/create", response_class=HTMLResponse)
def add_paiement_form(request: Request, facture_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_avocat_user)):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return templates.TemplateResponse("avocat/paiement/form_paiement.html", {
        "request": request,
        "facture": facture,
        "user": user
    })


@router.post("/factures/{facture_id}/paiements/create")
async def add_paiement(
        request: Request,
        facture_id: int,
        montant: float = Form(...),
        fichiers: Optional[List[UploadFile]] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    paiement = add_paiement_service(db, facture_id, user.id, montant, user.nom, fichiers)
    return RedirectResponse(url=f"/factures/{facture_id}", status_code=303)


@router.get("/factures/{facture_id}/paiements", response_class=HTMLResponse)
def list_paiements_form(request: Request, facture_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_avocat_user)):
    facture = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    paiements = get_paiements_by_facture_service(db, facture_id)
    return templates.TemplateResponse("avocat/paiement/liste_paiements.html", {
        "request": request,
        "facture": facture,
        "paiements": paiements,
        "user": user
    })


@router.get("/paiements/{paiement_id}/modifier", response_class=HTMLResponse)
def edit_paiement_form(request: Request, paiement_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_avocat_user)):
    paiement_repo = PaiementRepository(db)
    paiement = paiement_repo.get(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")

    return templates.TemplateResponse("avocat/paiement/form_edit_paiement.html", {
        "request": request,
        "paiement": paiement,
        "user": user
    })


@router.post("/paiements/{paiement_id}")
async def update_paiement(
        request: Request,
        paiement_id: int,
        montant: Optional[float] = Form(None),
        fichiers: Optional[List[UploadFile]] = File(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    paiement = update_paiement_service(db, paiement_id, montant, fichiers, user.nom)
    return RedirectResponse(url=f"/factures/{paiement.facture.id}/paiements", status_code=303)


@router.post("/paiements/{paiement_id}/delete")
def delete_paiement_web(
        paiement_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    paiement = PaiementRepository(db).get(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")

    delete_paiement_service(db, paiement_id)
    return RedirectResponse(
        url=f"/factures/{paiement.facture.id}",
        status_code=303
    )


@router.get("/paiements/{paiement_id}/download")
def download_paiement(paiement_id: int, db: Session = Depends(get_db)):
    paiement = PaiementRepository(db).get(paiement_id)
    if not paiement or not paiement.preuve_paiement:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    file_path = paiement.preuve_paiement
    file_name = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=file_name
    )


@router.post("/factures/{facture_id}/generer-solde")
async def generer_facture_solde(
        facture_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):
    facture_originale = facture_repo.get_facture_by_id(db, facture_id, user.id)
    if not facture_originale:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    if facture_originale.montant_restant <= 0:
        raise HTTPException(status_code=400, detail="Aucun montant restant à facturer")

    try:
        facture_solde_data = FactureCreate(
            dossier_id=facture_originale.dossier_id,
            nom_client_anonyme=facture_originale.nom_client_anonyme,
            description=f"SOLDE - {facture_originale.description}",
            montant_ht=facture_originale.montant_restant / (1 + facture_originale.taux_tva / 100),
            taux_tva=facture_originale.taux_tva,
            date_echeance=facture_originale.date_echeance,
            rappel_active=facture_originale.rappel_active,
            type_rappel=facture_originale.type_rappel,
            notes_internes=f"Facture de solde générée depuis la facture {facture_originale.numero_facture}",
            facture_parent_id=facture_originale.id
        )

        nouvelle_facture = facture_service.create_facture_with_file(
            db, facture_solde_data, user.id, user.nom
        )

        facture_update = FactureUpdate(
            notes_internes=f"{facture_originale.notes_internes or ''}\n[SOLDE FACTURÉ SÉPARÉMENT - Facture {nouvelle_facture.numero_facture}]"
        )
        facture_service.update_facture_with_files(
            db, facture_id, facture_update, user.id, user.nom
        )

        return RedirectResponse(
            url=f"/factures/{facture_id}?success=solde_generated",
            status_code=303
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du solde: {str(e)}")
