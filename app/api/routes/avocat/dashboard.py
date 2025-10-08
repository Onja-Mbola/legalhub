from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.auth import get_current_avocat_user, get_current_clerk_user
from app.core.enums import RoleEnum
from app.db.session import get_db
from app.models.action_log import ActionLog
from app.models.user import User
from app.services.dashboard_service import get_dashboard_data, get_statistiques_detaillees
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage
from app.services.dossier import get_dossiers_by_user_service, get_dossiers_archiver_by_user_service

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
        "dossiers_recents": get_recent_dossiers_with_progress(db, user)
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


def get_recent_dossiers_with_progress(db: Session, user: User, limit: int = 5):
    if user.role == RoleEnum.avocat:
        dossiers = db.query(Dossier).filter(
            Dossier.avocat_responsable == user.id
        ).order_by(Dossier.date_creation.desc()).limit(limit).all()
    elif user.role == RoleEnum.clerk:
        if not user.created_by_id:
            return []
        dossiers = db.query(Dossier).filter(
            Dossier.avocat_responsable == user.created_by_id
        ).order_by(Dossier.date_creation.desc()).limit(limit).all()
    else:
        return []

    stage_progress = {
        ProcessStage.INTRODUCTION_INSTANCE.value: 5,
        ProcessStage.ENROLEMENT.value: 10,
        ProcessStage.REQUETE_ASSIGNATION.value: 15,
        ProcessStage.PREMIERE_AUDIENCE.value: 25,
        ProcessStage.ECHANGE_CONCLUSIONS.value: 40,
        ProcessStage.DELIBERATION.value: 55,
        ProcessStage.DECISION_AVANT_DIRE_DROIT.value: 45,
        ProcessStage.DECISION_DEFINITIVE.value: 70,

        ProcessStage.JUGEMENT_FAVORABLE.value: 75,
        ProcessStage.NOTIFICATION_CLIENT.value: 85,
        ProcessStage.RECUPERATION_GROSSE.value: 95,

        ProcessStage.JUGEMENT_DEFAVORABLE.value: 72,
        ProcessStage.JUGEMENT_CONTRADICTOIRE.value: 73,
        ProcessStage.PAR_DEFAUT.value: 50,
        ProcessStage.OPPOSITION.value: 55,
        ProcessStage.RETOUR_AUDIENCE.value: 60,
        ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT.value: 65,
        ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT.value: 75,
        ProcessStage.JUGEMENT_DEFINITIF.value: 85,
        ProcessStage.NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT.value: 95,

        ProcessStage.APPEL.value: 40,
        ProcessStage.ENROLEMENT_APPEL.value: 45,
        ProcessStage.PREMIERE_AUDIENCE_APPEL.value: 50,
        ProcessStage.ECHANGE_CONCLUSIONS_APPEL.value: 60,
        ProcessStage.DELIBERATION_APPEL.value: 70,
        ProcessStage.AVANT_DIRE_DROIT.value: 65,
        ProcessStage.FOND.value: 80,
        ProcessStage.CASSATION.value: 75,

        ProcessStage.FIN_ARCHIVAGE.value: 100
    }

    for dossier in dossiers:
        dossier.progress = stage_progress.get(dossier.current_stage, 10)

    return dossiers


def get_dossier_progress_percentage(dossier: Dossier) -> int:
    stage_progress = {
        ProcessStage.INTRODUCTION_INSTANCE.value: 5,
        ProcessStage.ENROLEMENT.value: 10,
        ProcessStage.REQUETE_ASSIGNATION.value: 15,
        ProcessStage.PREMIERE_AUDIENCE.value: 25,
        ProcessStage.ECHANGE_CONCLUSIONS.value: 40,
        ProcessStage.DELIBERATION.value: 55,
        ProcessStage.DECISION_AVANT_DIRE_DROIT.value: 45,
        ProcessStage.DECISION_DEFINITIVE.value: 70,
        ProcessStage.JUGEMENT_FAVORABLE.value: 75,
        ProcessStage.NOTIFICATION_CLIENT.value: 85,
        ProcessStage.RECUPERATION_GROSSE.value: 95,
        ProcessStage.JUGEMENT_DEFAVORABLE.value: 72,
        ProcessStage.JUGEMENT_CONTRADICTOIRE.value: 73,
        ProcessStage.PAR_DEFAUT.value: 50,
        ProcessStage.OPPOSITION.value: 55,
        ProcessStage.RETOUR_AUDIENCE.value: 60,
        ProcessStage.ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT.value: 65,
        ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT.value: 75,
        ProcessStage.JUGEMENT_DEFINITIF.value: 85,
        ProcessStage.NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT.value: 95,
        ProcessStage.APPEL.value: 40,
        ProcessStage.ENROLEMENT_APPEL.value: 45,
        ProcessStage.PREMIERE_AUDIENCE_APPEL.value: 50,
        ProcessStage.ECHANGE_CONCLUSIONS_APPEL.value: 60,
        ProcessStage.DELIBERATION_APPEL.value: 70,
        ProcessStage.AVANT_DIRE_DROIT.value: 65,
        ProcessStage.FOND.value: 80,
        ProcessStage.CASSATION.value: 75,
        ProcessStage.FIN_ARCHIVAGE.value: 100
    }

    return stage_progress.get(dossier.current_stage, 10)


@router.get("/clerk/dashboard", response_class=HTMLResponse)
def clerk_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_clerk_user)
):
    dossiers = get_dossiers_by_user_service(db, user)
    dossiers_archives = get_dossiers_archiver_by_user_service(db, user)

    active_cases_count = len(dossiers)
    archived_cases_count = len(dossiers_archives)

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    active_cases_monthly = len([
        d for d in dossiers
        if d.date_creation and d.date_creation.month == current_month and d.date_creation.year == current_year
    ])

    dossiers_recents = get_recent_dossiers_with_progress(db, user, limit=5)

    cases_by_type = {}
    for dossier in dossiers:
        if dossier.type_affaire_param:
            type_affaire = dossier.type_affaire_param.valeur
            cases_by_type[type_affaire] = cases_by_type.get(type_affaire, 0) + 1

    recent_activities = (
        db.query(ActionLog)
        .filter(ActionLog.user_id == user.id)
        .order_by(ActionLog.created_at.desc())
        .limit(10)
        .all()
    )

    created_by_user = None
    avocat_nom = None
    if user.created_by_id:
        created_by_user = db.query(User).filter(User.id == user.created_by_id).first()
        if created_by_user:
            avocat_nom = created_by_user.nom

    return templates.TemplateResponse("clerk/dashboard_clerk.html", {
        "request": request,
        "user": user,
        "active_cases_count": active_cases_count,
        "archived_cases_count": archived_cases_count,
        "active_cases_monthly": active_cases_monthly,
        "dossiers_recents": dossiers_recents,
        "cases_by_type": cases_by_type,
        "recent_activities": recent_activities,
        "created_by_user": created_by_user,
        "avocat_nom": avocat_nom
    })