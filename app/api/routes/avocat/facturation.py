from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional

from app.core.auth import get_current_avocat_user
from app.db.session import get_db
from app.models.user import User
from app.services.dashboard_service import get_dashboard_data, get_statistiques_detaillees
from app.services.pdf_generator import generate_rapport_facturation_pdf
from app.repositories.facture import get_factures_by_avocat

router = APIRouter()


@router.get("/api/reports/facturation")
async def generate_facturation_report(
        period: str = Query("current_month"),
        include_charts: bool = Query(True),
        include_factures: bool = Query(True),
        include_clients: bool = Query(False),
        date_debut: Optional[str] = Query(None),
        date_fin: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    try:
        dashboard_data = get_dashboard_data(db, user.id)
        stats_detaillees = get_statistiques_detaillees(db, user.id, datetime.now().year)

        factures = get_factures_by_avocat(db, user.id, 0, 1000) if include_factures else []

        report_data = {
            'period': period,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'stats_facturation': dashboard_data['stats_facturation'],
            'revenus_mensuels': dashboard_data['revenus_mensuels'] if include_charts else {},
            'sources_revenus': dashboard_data['sources_revenus'] if include_charts else {},
            'factures': factures,
            'top_clients': dashboard_data['top_clients'] if include_clients else [],
            'avocat_nom': user.nom,
            'date_generation': datetime.now()
        }

        pdf_content = generate_rapport_facturation_pdf(report_data)

        filename = f"rapport_facturation_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        return {"error": f"Erreur lors de la génération du rapport: {str(e)}"}


@router.get("/api/dashboard/data")
async def get_dashboard_api_data(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    try:
        dashboard_data = get_dashboard_data(db, user.id)

        return {
            "revenus_mensuels": dashboard_data['revenus_mensuels'],
            "sources_revenus": dashboard_data['sources_revenus'],
            "stats_facturation": {
                "total_facture": float(dashboard_data['stats_facturation'].total_facture),
                "total_paye": float(dashboard_data['stats_facturation'].total_paye),
                "total_impaye": float(dashboard_data['stats_facturation'].total_impaye),
                "nombre_factures_total": dashboard_data['stats_facturation'].nombre_factures_total,
                "nombre_factures_payees": dashboard_data['stats_facturation'].nombre_factures_payees,
                "nombre_factures_impayees": dashboard_data['stats_facturation'].nombre_factures_impayees,
                "taux_recouvrement": float(dashboard_data['stats_facturation'].taux_recouvrement)
            },
            "factures_en_retard_count": len(dashboard_data['factures_en_retard']),
            "top_clients": dashboard_data['top_clients']
        }

    except Exception as e:
        return {"error": f"Erreur lors de la récupération des données: {str(e)}"}


@router.get("/api/stats/evolution")
async def get_evolution_stats(
        periode: str = Query("12months"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    try:
        from app.services.dashboard_service import get_evolution_taux_recouvrement

        current_year = datetime.now().year
        evolution_data = get_evolution_taux_recouvrement(db, user.id, current_year)

        return {
            "evolution_recouvrement": evolution_data,
            "periode": periode,
            "annee": current_year
        }

    except Exception as e:
        return {"error": f"Erreur lors de la récupération de l'évolution: {str(e)}"}


@router.post("/api/dashboard/refresh")
async def refresh_dashboard_data(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_avocat_user)
):

    try:
        dashboard_data = get_dashboard_data(db, user.id)

        return {
            "status": "success",
            "message": "Données mises à jour",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total_factures": dashboard_data['stats_facturation'].nombre_factures_total,
                "revenus_mois": sum(dashboard_data['revenus_mensuels'].values()),
                "taux_recouvrement": dashboard_data['stats_facturation'].taux_recouvrement
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors du rafraîchissement: {str(e)}"
        }