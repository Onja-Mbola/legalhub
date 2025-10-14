from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Type

from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session

from app.models.dossier import Dossier
from app.models.facture import Facture, StatutFacture, TypeRappel
from app.schemas.facture import FactureCreate, FactureUpdate, StatistiqueFacturation, StatistiqueRevenu


def generate_numero_facture(db: Session, avocat_id: int) -> str:
    current_year = datetime.now().year
    count = db.query(Facture).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_creation) == current_year
    ).count()
    return f"FACT-{current_year}-{avocat_id:03d}-{count + 1:04d}"


def create_facture(db: Session, facture: FactureCreate, avocat_id: int) -> Facture:
    montant_ttc = facture.montant_ht * (1 + facture.taux_tva / 100)

    prochaine_relance = None
    if facture.rappel_active and facture.type_rappel != TypeRappel.AUCUN:
        prochaine_relance = calculate_next_reminder(facture.type_rappel, facture.date_echeance)

    db_facture = Facture(
        numero_facture=generate_numero_facture(db, avocat_id),
        dossier_id=facture.dossier_id,
        nom_client_anonyme=facture.nom_client_anonyme,
        description=facture.description,
        montant_ht=facture.montant_ht,
        taux_tva=facture.taux_tva,
        montant_ttc=montant_ttc,
        date_echeance=facture.date_echeance,
        rappel_active=facture.rappel_active,
        type_rappel=facture.type_rappel,
        prochaine_relance=prochaine_relance,
        notes_internes=facture.notes_internes,
        facture_parent_id=facture.facture_parent_id
    )

    db.add(db_facture)
    db.commit()
    db.refresh(db_facture)
    return db_facture


def get_factures_by_avocat(db: Session, avocat_id: int, skip: int = 0, limit: int = 100) -> List[Facture]:
    return db.query(Facture).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id
    ).offset(skip).limit(limit).all()


def get_facture_by_id(db: Session, facture_id: int, avocat_id: int) -> Optional[Facture]:
    return db.query(Facture).join(Dossier).filter(
        Facture.id == facture_id,
        Dossier.avocat_responsable == avocat_id
    ).first()


def get_factures_by_dossier(db: Session, dossier_id: int) -> List[Facture]:
    return db.query(Facture).filter(Facture.dossier_id == dossier_id).all()


def update_facture(db: Session, facture_id: int, facture_update: FactureUpdate, avocat_id: int) -> Optional[Facture]:
    facture = get_facture_by_id(db, facture_id, avocat_id)
    if not facture:
        return None

    update_data = facture_update.dict(exclude_unset=True)

    if "montant_ht" in update_data or "taux_tva" in update_data:
        montant_ht = update_data.get("montant_ht") if update_data.get("montant_ht") is not None else facture.montant_ht
        taux_tva = update_data.get("taux_tva") if update_data.get("taux_tva") is not None else (facture.taux_tva or 0)
        update_data["montant_ttc"] = montant_ht * (1 + taux_tva / 100)

    rappel_active = update_data.get("rappel_active", facture.rappel_active)
    type_rappel = update_data.get("type_rappel", facture.type_rappel)
    date_echeance = update_data.get("date_echeance", facture.date_echeance)

    if rappel_active and type_rappel != TypeRappel.AUCUN:
        update_data["prochaine_relance"] = calculate_next_reminder(type_rappel, date_echeance)
    else:
        update_data["prochaine_relance"] = None

    if update_data.get("statut") == StatutFacture.PAYEE and not facture.date_paiement:
        update_data["date_paiement"] = datetime.utcnow()

    for field, value in update_data.items():
        if value is not None:
            setattr(facture, field, value)

    db.commit()
    db.refresh(facture)
    return facture


def delete_facture(db: Session, facture_id: int, avocat_id: int) -> bool:
    facture = get_facture_by_id(db, facture_id, avocat_id)
    if facture:
        db.delete(facture)
        db.commit()
        return True
    return False


def get_factures_en_attente_relance(db: Session) -> list[Type[Facture]]:
    now = datetime.utcnow()
    return db.query(Facture).filter(
        and_(
            Facture.rappel_active == True,
            Facture.statut.in_([StatutFacture.ENVOYEE, StatutFacture.EN_RETARD]),
            Facture.prochaine_relance <= now
        )
    ).all()


def update_relance_facture(db: Session, facture_id: int):
    facture = db.query(Facture).filter(Facture.id == facture_id).first()
    if facture and facture.rappel_active:
        facture.nombre_relances += 1

        if facture.type_rappel == TypeRappel.HEBDOMADAIRE:
            facture.prochaine_relance = datetime.utcnow() + timedelta(weeks=1)
        elif facture.type_rappel == TypeRappel.MENSUEL:
            facture.prochaine_relance = datetime.utcnow() + timedelta(days=30)
        elif facture.type_rappel == TypeRappel.FIN_MOIS:
            next_month = datetime.utcnow().replace(day=1) + timedelta(days=32)
            facture.prochaine_relance = next_month.replace(day=1) - timedelta(days=1)

        if facture.date_echeance < datetime.utcnow().date() and facture.statut == StatutFacture.ENVOYEE:
            facture.statut = StatutFacture.EN_RETARD

        db.commit()


def get_statistiques_facturation(db: Session, avocat_id: int, annee: Optional[int] = None) -> StatistiqueFacturation:
    query = db.query(Facture).join(Dossier).filter(Dossier.avocat_responsable == avocat_id , Facture.facture_parent_id.is_(None))

    if annee:
        query = query.filter(extract('year', Facture.date_creation) == annee)

    factures = query.all()

    total_facture = sum(f.montant_ttc for f in factures)
    factures_payees = [f for f in factures if f.statut == StatutFacture.PAYEE]
    total_paye = sum(f.montant_ttc for f in factures_payees)
    total_impaye = total_facture - total_paye

    taux_recouvrement = (total_paye / total_facture * 100) if total_facture > 0 else 0

    recouvrement_par_mois = defaultdict(float)
    for f in factures_payees:
        if f.date_emission:
            recouvrement_par_mois[str(f.date_emission.month)] += f.montant_ttc

    return StatistiqueFacturation(
        total_facture=total_facture,
        total_paye=total_paye,
        total_impaye=total_impaye,
        nombre_factures_total=len(factures),
        nombre_factures_payees=len(factures_payees),
        nombre_factures_impayees=len(factures) - len(factures_payees),
        taux_recouvrement=round(taux_recouvrement, 2),
        recouvrement_par_mois = dict(recouvrement_par_mois)
    )


def get_statistiques_revenus(db: Session, avocat_id: int, annee: int) -> StatistiqueRevenu:
    revenus_mois = db.query(
        extract('month', Facture.date_paiement).label('mois'),
        func.sum(Facture.montant_ttc).label('total')
    ).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_paiement) == annee,
        Facture.statut == StatutFacture.PAYEE,
        Facture.facture_parent_id.is_(None)
    ).group_by(extract('month', Facture.date_paiement)).all()

    revenus_par_mois = {str(int(r.mois)): float(r.total) for r in revenus_mois}

    revenus_type = db.query(
        Dossier.type_affaire,
        func.sum(Facture.montant_ttc).label('total')
    ).join(Facture).filter(
        Dossier.avocat_responsable == avocat_id,
        extract('year', Facture.date_paiement) == annee,
        Facture.statut == StatutFacture.PAYEE,
        Facture.facture_parent_id.is_(None)
    ).group_by(Dossier.type_affaire).all()

    revenus_par_type_affaire = {str(r.type_affaire): float(r.total) for r in revenus_type}

    return StatistiqueRevenu(
        revenus_par_mois=revenus_par_mois,
        revenus_par_type_affaire=revenus_par_type_affaire,
        evolution_mensuelle={}
    )



def calculate_next_reminder(type_rappel: TypeRappel, date_echeance) -> Optional[datetime]:
    if isinstance(date_echeance, str):
        date_echeance = datetime.strptime(date_echeance, "%Y-%m-%d").date()

    date_echeance_dt = datetime.combine(date_echeance, datetime.min.time())

    if type_rappel == TypeRappel.HEBDOMADAIRE:
        return date_echeance_dt + timedelta(weeks=1)
    elif type_rappel == TypeRappel.MENSUEL:
        return date_echeance_dt + timedelta(days=30)
    elif type_rappel == TypeRappel.FIN_MOIS:
        next_month = date_echeance_dt.replace(day=1) + timedelta(days=32)
        return next_month.replace(day=1) - timedelta(days=1)

    return None


def get_factures_en_retard(db: Session, avocat_id: int) -> list[Type[Facture]]:
    today = datetime.now()

    return db.query(Facture).join(Dossier).filter(
        Dossier.avocat_responsable == avocat_id,
        Facture.statut.in_([StatutFacture.ENVOYEE, StatutFacture.EN_RETARD]),
        Facture.date_echeance < today
    ).order_by(Facture.date_echeance.asc()).all()


def get_top_clients(db: Session, avocat_id: int, limit: int = 5) -> List[dict]:
    try:
        results = db.query(
            Facture.nom_client_anonyme,
            func.sum(Facture.montant_ttc).label('total_revenus'),
            func.count(Facture.id).label('nb_factures')
        ).join(Dossier).filter(
            Dossier.avocat_responsable == avocat_id,
            Facture.statut == StatutFacture.PAYEE,
            Facture.facture_parent_id.is_(None)
        ).group_by(
            Facture.nom_client_anonyme
        ).order_by(
            func.sum(Facture.montant_ttc).desc()
        ).limit(limit).all()

        return [
            {
                'nom_client_anonyme': r.nom_client_anonyme,
                'total_revenus': float(r.total_revenus),
                'nb_factures': r.nb_factures
            }
            for r in results
        ]
    except Exception as e:
        print(f"Erreur get_top_clients: {e}")
        return []


def get_delai_paiement_moyen(db: Session, avocat_id: int) -> str:
    try:
        factures_payees = db.query(Facture).join(Dossier).filter(
            Dossier.avocat_responsable == avocat_id,
            Facture.statut == StatutFacture.PAYEE,
            Facture.date_paiement.is_not(None),
            Facture.date_emission.is_not(None)
        ).all()

        if not factures_payees:
            return "N/A"

        total_jours = 0
        count = 0

        for facture in factures_payees:
            if facture.date_paiement and facture.date_emission:
                delta = facture.date_paiement.date() - facture.date_emission.date()
                total_jours += delta.days
                count += 1

        if count == 0:
            return "N/A"

        moyenne = total_jours / count
        return f"{moyenne:.1f} jours"

    except Exception as e:
        print(f"Erreur calcul délai paiement: {e}")
        return "N/A"


def get_statistiques_facturation_complete(db: Session, avocat_id: int, annee: Optional[int] = None) -> dict:
    try:
        stats_base = get_statistiques_facturation(db, avocat_id, annee)

        stats_revenus = get_statistiques_revenus(db, avocat_id, annee or datetime.now().year)

        factures_en_retard = get_factures_en_retard(db, avocat_id)
        top_clients = get_top_clients(db, avocat_id, 5)
        delai_paiement_moyen = get_delai_paiement_moyen(db, avocat_id)

        recouvrement_par_mois = {}
        if annee:
            for mois in range(1, 13):
                factures_mois = db.query(Facture).join(Dossier).filter(
                    Dossier.avocat_responsable == avocat_id,
                    extract('year', Facture.date_creation) == annee,
                    extract('month', Facture.date_creation) == mois,
                    Facture.facture_parent_id.is_(None)
                ).all()

                if factures_mois:
                    total_mois = sum(f.montant_ttc for f in factures_mois)
                    paye_mois = sum(f.montant_ttc for f in factures_mois if f.statut == StatutFacture.PAYEE)
                    taux = (paye_mois / total_mois * 100) if total_mois > 0 else 0
                    recouvrement_par_mois[str(mois)] = round(taux, 1)
                else:
                    recouvrement_par_mois[str(mois)] = 0

        if hasattr(stats_base, 'recouvrement_par_mois'):
            stats_base.recouvrement_par_mois = recouvrement_par_mois

        return {
            'stats_facturation': stats_base,
            'stats_revenus': stats_revenus,
            'factures_en_retard': factures_en_retard,
            'top_clients': top_clients,
            'delai_paiement_moyen': delai_paiement_moyen
        }

    except Exception as e:
        print(f"Erreur get_statistiques_facturation_complete: {e}")
        return {
            'stats_facturation': None,
            'stats_revenus': None,
            'factures_en_retard': [],
            'top_clients': [],
            'delai_paiement_moyen': "N/A"
        }
