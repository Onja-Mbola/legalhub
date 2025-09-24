from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.dashboard_service import get_dashboard_data, get_statistiques_detaillees
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/avocat/dashboard", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def dashboard(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    dashboard_data = get_dashboard_data(db, user.id)

    context = {
        "request": request,
        "user": user,

        "stats_facturation": dashboard_data['stats_facturation'],
        "active_cases_monthly": dashboard_data['stats_dossiers']['dossiers_actifs_mois'],
        "closed_cases_annual": dashboard_data['stats_dossiers']['dossiers_annee'],
        "new_clients_monthly": dashboard_data['stats_dossiers']['nouveaux_clients_mois'],

        "revenus_mensuels": dashboard_data['revenus_mensuels'],
        "sources_revenus": dashboard_data['sources_revenus'],

        "factures_recentes": dashboard_data['factures_recentes'],
        "factures_en_retard": dashboard_data['factures_en_retard'],
        "top_clients": dashboard_data['top_clients'],

        "tasks_percentage": calculate_tasks_percentage(dashboard_data),
        "dossiers_recents": get_recent_dossiers_with_progress(db, user.id)
    }

    return templates.TemplateResponse("dashboard_avocat.html", context)


@router.get("/statistiques/facturations", response_class=HTMLResponse)
def statistiques_facturation(
        request: Request,
        annee: int = None,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    if not annee:
        annee = datetime.now().year

    dashboard_data = get_dashboard_data(db, user.id)
    stats_detaillees = get_statistiques_detaillees(db, user.id, annee)

    context = {
        "request": request,
        "user": user,
        "annee": annee,

        "stats_facturation": dashboard_data['stats_facturation'],

        "revenus_mensuels": dashboard_data['revenus_mensuels'],
        "sources_revenus": dashboard_data['sources_revenus'],
        "evolution_recouvrement": stats_detaillees['evolution_recouvrement'],

        "top_clients": dashboard_data['top_clients'],
        "factures_en_retard": dashboard_data['factures_en_retard'],

        "delai_paiement_moyen": stats_detaillees['delai_paiement_moyen'],
        "montant_moyen_facture": stats_detaillees['montant_moyen_facture']
    }

    return templates.TemplateResponse("avocat/facture/statistiques.html", context)


def calculate_tasks_percentage(dashboard_data) -> int:
    stats = dashboard_data['stats_facturation']
    if stats.nombre_factures_total > 0:
        return min(100, int(stats.taux_recouvrement))
    return 0


def get_recent_dossiers_with_progress(db: Session, avocat_id: int, limit: int = 5):

    dossiers = db.query(Dossier).filter(
        Dossier.avocat_responsable == avocat_id
    ).order_by(Dossier.date_creation.desc()).limit(limit).all()

    stage_progress = {
        ProcessStage.INTRODUCTION_INSTANCE.value: 10,
        ProcessStage.ENROLEMENT.value: 20,
        ProcessStage.PREMIERE_AUDIENCE.value: 40,
        ProcessStage.ECHANGE_CONCLUSIONS.value: 60,
        ProcessStage.DELIBERATION.value: 80,
        ProcessStage.JUGEMENT_DEFINITIF.value: 90,
        ProcessStage.FIN_ARCHIVAGE.value: 100
    }

    for dossier in dossiers:
        dossier.progress = stage_progress.get(dossier.current_stage, 15)

    return dossiers