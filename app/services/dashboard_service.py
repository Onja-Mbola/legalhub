from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case
from typing import Dict, List, Any, Type
from app.models.facture import Facture, StatutFacture
from app.models.dossier import Dossier
from app.models.param_general import ParamGeneral
from app.repositories.facture import get_statistiques_facturation


def get_dashboard_data(db: Session, avocat_id: int) -> Dict[str, Any]:

    current_year = datetime.now().year
    current_month = datetime.now().month

    stats_facturation = get_statistiques_facturation(db, avocat_id, current_year)

    revenus_mensuels = get_revenus_mensuels(db, avocat_id, current_year)

    sources_revenus = get_revenus_par_type_affaire(db, avocat_id, current_year)

    factures_recentes = get_factures_recentes(db, avocat_id, limit=5)

    factures_en_retard = get_factures_en_retard(db, avocat_id)

    stats_dossiers = get_statistiques_dossiers(db, avocat_id)

    top_clients = get_top_clients_anonymes(db, avocat_id, limit=5)

    return {
        'stats_facturation': stats_facturation,
        'revenus_mensuels': revenus_mensuels,
        'sources_revenus': sources_revenus,
        'factures_recentes': factures_recentes,
        'factures_en_retard': factures_en_retard,
        'stats_dossiers': stats_dossiers,
        'top_clients': top_clients
    }


def get_revenus_mensuels(db: Session, avocat_id: int, annee: int) -> Dict[str, float]:

    revenus = db.query(
        extract('month', Facture.date_paiement).label('mois'),
        func.sum(Facture.montant_ttc).label('total')
    ).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_paiement) == annee,
        Facture.statut == StatutFacture.PAYEE,
        Facture.date_paiement.isnot(None)
    ).group_by(extract('month', Facture.date_paiement)).all()

    revenus_dict = {}
    for mois in range(1, 13):
        revenus_dict[str(mois)] = 0.0

    for revenu in revenus:
        revenus_dict[str(int(revenu.mois))] = float(revenu.total or 0)

    return revenus_dict


def get_revenus_par_type_affaire(db: Session, avocat_id: int, annee: int) -> Dict[str, float]:

    revenus = db.query(
        ParamGeneral.valeur.label('type_affaire'),
        func.sum(Facture.montant_ttc).label('total')
    ).join(Dossier, Facture.dossier_id == Dossier.id) \
        .join(ParamGeneral, Dossier.type_affaire == ParamGeneral.id) \
        .filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_paiement) == annee,
        Facture.statut == StatutFacture.PAYEE,
        Facture.date_paiement.isnot(None)
    ).group_by(ParamGeneral.valeur).all()

    revenus_dict = {}
    for revenu in revenus:
        if revenu.type_affaire and revenu.total:
            revenus_dict[revenu.type_affaire] = float(revenu.total)

    return revenus_dict


def get_factures_recentes(db: Session, avocat_id: int, limit: int = 10) -> List[Facture]:

    return db.query(Facture).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id
    ).order_by(Facture.date_creation.desc()).limit(limit).all()


def get_factures_en_retard(db: Session, avocat_id: int) -> list[Type[Facture]]:

    today = date.today()
    return db.query(Facture).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        Facture.date_echeance < today,
        Facture.statut.in_([StatutFacture.ENVOYEE, StatutFacture.EN_RETARD])
    ).order_by(Facture.date_echeance.asc()).all()


def get_statistiques_dossiers(db: Session, avocat_id: int) -> Dict[str, int]:

    current_month = datetime.now().replace(day=1)
    current_year = datetime.now().year

    dossiers_actifs_mois = db.query(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        Dossier.date_creation >= current_month
    ).count()

    dossiers_annee = db.query(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Dossier.date_creation) == current_year
    ).count()

    nouveaux_clients = db.query(Dossier.client_id).filter(
        Dossier.avocat_responsable == avocat_id,
        Dossier.date_creation >= current_month
    ).distinct().count()

    return {
        'dossiers_actifs_mois': dossiers_actifs_mois,
        'dossiers_annee': dossiers_annee,
        'nouveaux_clients_mois': nouveaux_clients
    }


def get_top_clients_anonymes(db: Session, avocat_id: int, limit: int = 5) -> List[Dict[str, Any]]:

    clients = db.query(
        Facture.nom_client_anonyme,
        func.sum(Facture.montant_ttc).label('total_revenus'),
        func.count(Facture.id).label('nb_factures')
    ).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        Facture.statut == StatutFacture.PAYEE
    ).group_by(Facture.nom_client_anonyme) \
        .order_by(func.sum(Facture.montant_ttc).desc()) \
        .limit(limit).all()

    return [
        {
            'nom_client_anonyme': client.nom_client_anonyme,
            'total_revenus': float(client.total_revenus or 0),
            'nb_factures': int(client.nb_factures or 0)
        }
        for client in clients
    ]


def get_evolution_taux_recouvrement(db: Session, avocat_id: int, annee: int) -> Dict[str, float]:

    taux_mensuels = {}

    for mois in range(1, 13):
        factures_emises = db.query(Facture).join(Dossier).filter(
            Dossier.avocat_responsable == avocat_id,
            extract('year', Facture.date_emission) == annee,
            extract('month', Facture.date_emission) == mois,
            Facture.date_emission.isnot(None)
        ).count()

        factures_payees = db.query(Facture).join(Dossier).filter(
            Dossier.avocat_responsable == avocat_id,
            extract('year', Facture.date_emission) == annee,
            extract('month', Facture.date_emission) == mois,
            Facture.statut == StatutFacture.PAYEE,
            Facture.date_emission.isnot(None)
        ).count()

        taux = (factures_payees / factures_emises * 100) if factures_emises > 0 else 0
        taux_mensuels[str(mois)] = round(taux, 1)

    return taux_mensuels


def get_statistiques_detaillees(db: Session, avocat_id: int, annee: int) -> Dict[str, Any]:

    delais = db.query(
        func.avg(
            func.date_part('day', Facture.date_paiement - Facture.date_emission)
        ).label('delai_moyen')
    ).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        Facture.statut == StatutFacture.PAYEE,
        Facture.date_paiement.isnot(None),
        Facture.date_emission.isnot(None),
        extract('year', Facture.date_paiement) == annee
    ).scalar()

    delai_moyen = f"{int(delais or 0)} jours" if delais else "N/A"

    montant_moyen = db.query(
        func.avg(Facture.montant_ttc).label('moyenne')
    ).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_creation) == annee
    ).scalar()

    return {
        'delai_paiement_moyen': delai_moyen,
        'montant_moyen_facture': float(montant_moyen or 0),
        'evolution_recouvrement': get_evolution_taux_recouvrement(db, avocat_id, annee)
    }