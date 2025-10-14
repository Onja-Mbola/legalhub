from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.repositories.clients import (
    get_clients_by_avocat,
    get_client_by_id,
    get_client_stats
)
from app.models.client import Client
from app.models.demandeur import Demandeur
from app.models.dossier import Dossier


def get_all_clients_for_avocat(db: Session, avocat_id: int) -> List[Client]:
    """
    Récupère tous les clients accessibles par un avocat :
    - Clients avec avocat_id = avocat_id
    - Clients liés à des dossiers de l'avocat (même sans avocat_id)
    """
    # Méthode 1 : Clients directs
    clients_directs = db.query(Client).filter(
        Client.avocat_id == avocat_id
    ).all()

    # Méthode 2 : Clients via dossiers (pour ceux sans avocat_id)
    clients_via_dossiers = db.query(Client).join(
        Dossier, Client.id == Dossier.client_id
    ).filter(
        Dossier.avocat_responsable == avocat_id,
        or_(Client.avocat_id == None, Client.avocat_id != avocat_id)
    ).all()

    # Combiner et dédupliquer
    all_clients = clients_directs + clients_via_dossiers
    clients_uniques = list({c.id: c for c in all_clients}.values())

    return clients_uniques


def get_clients_list_service(
        db: Session,
        avocat_id: int,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        sort_by: str = "nom",
        order: str = "asc"
) -> dict:
    skip = (page - 1) * per_page
    clients, total = get_clients_by_avocat(
        db, avocat_id, skip, per_page, search, sort_by, order
    )

    clients_data = []
    for client in clients:
        stats = get_client_stats(db, client.id)

        # Chercher le demandeur principal via client_id
        demandeur_principal = db.query(Demandeur).filter(
            Demandeur.client_id == client.id
        ).first()

        # Si pas de demandeur avec client_id, prendre le premier du premier dossier
        if not demandeur_principal and client.dossiers:
            premier_dossier = client.dossiers[0]
            demandeur_principal = db.query(Demandeur).filter(
                Demandeur.dossier_id == premier_dossier.id
            ).first()

        client_info = {
            "client": client,
            "stats": stats,
            "demandeur_principal": demandeur_principal
        }
        clients_data.append(client_info)

    total_pages = (total + per_page - 1) // per_page

    return {
        "clients": clients_data,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    }


def get_client_detail_service(db: Session, client_id: int, avocat_id: int) -> Optional[dict]:
    # Récupérer le client
    client = get_client_by_id(db, client_id)

    if not client:
        return None

    # Vérification de l'accès :
    # 1. Si le client a un avocat_id, il doit correspondre
    # 2. Sinon, vérifier via les dossiers (pour rétrocompatibilité)
    if client.avocat_id:
        if client.avocat_id != avocat_id:
            return None
    else:
        # Vérifier via les dossiers si pas d'avocat_id
        if not client.dossiers or not any(d.avocat_responsable == avocat_id for d in client.dossiers):
            return None

    stats = get_client_stats(db, client_id)

    # Méthode 1 : demandeurs liés directement au client
    demandeurs_direct = db.query(Demandeur).filter(
        Demandeur.client_id == client_id
    ).all()

    # Méthode 2 : demandeurs via les dossiers du client
    demandeurs_dossiers = []
    for dossier in client.dossiers:
        demandeurs = db.query(Demandeur).filter(
            Demandeur.dossier_id == dossier.id
        ).all()
        demandeurs_dossiers.extend(demandeurs)

    # Combiner et dédupliquer par ID
    all_demandeurs = demandeurs_direct + demandeurs_dossiers
    demandeurs_uniques = list({d.id: d for d in all_demandeurs}.values())

    return {
        "client": client,
        "stats": stats,
        "demandeurs": demandeurs_uniques,
        "dossiers": sorted(
            client.dossiers,
            key=lambda d: d.date_creation if d.date_creation else d.id,
            reverse=True
        )
    }


def export_clients_csv(db: Session, avocat_id: int) -> str:
    import csv
    import io

    clients, _ = get_clients_by_avocat(db, avocat_id, skip=0, limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Nom", "Email", "Téléphone", "Adresse",
        "Type", "Nombre de dossiers", "Statut"
    ])

    for client in clients:
        stats = get_client_stats(db, client.id)

        # Chercher le demandeur principal
        demandeur = db.query(Demandeur).filter(
            Demandeur.client_id == client.id
        ).first()

        # Si pas de demandeur via client_id, chercher dans le premier dossier
        if not demandeur and client.dossiers:
            demandeur = db.query(Demandeur).filter(
                Demandeur.dossier_id == client.dossiers[0].id
            ).first()

        statut_label = {
            "gros_client": "Gros client",
            "client_regulier": "Client régulier",
            "nouveau_client": "Nouveau client"
        }.get(stats.get("statut", ""), "")

        writer.writerow([
            client.id,
            demandeur.nom if demandeur and demandeur.nom else client.nom,
            demandeur.email if demandeur and demandeur.email else client.email,
            demandeur.telephone if demandeur and demandeur.telephone else client.telephone,
            client.adresse or "",
            client.qualite or "",
            stats.get("total_dossiers", 0),
            statut_label
        ])

    return output.getvalue()


def sync_client_avocat_id(db: Session, client_id: int) -> bool:
    """
    Synchronise l'avocat_id d'un client basé sur ses dossiers.
    Utile pour les clients créés avant l'ajout du champ avocat_id.

    Returns:
        bool: True si mis à jour, False sinon
    """
    client = get_client_by_id(db, client_id)

    if not client or client.avocat_id:
        return False

    # Trouver l'avocat le plus fréquent dans les dossiers du client
    if client.dossiers:
        avocat_counts = {}
        for dossier in client.dossiers:
            avocat_id = dossier.avocat_responsable
            avocat_counts[avocat_id] = avocat_counts.get(avocat_id, 0) + 1

        # Prendre l'avocat avec le plus de dossiers
        avocat_principal = max(avocat_counts, key=avocat_counts.get)
        client.avocat_id = avocat_principal
        db.commit()
        return True

    return False


def sync_all_clients_avocat_id(db: Session) -> int:
    """
    Synchronise tous les clients sans avocat_id.
    À exécuter une fois pour la migration.

    Returns:
        int: Nombre de clients mis à jour
    """
    clients_sans_avocat = db.query(Client).filter(
        Client.avocat_id == None
    ).all()

    count = 0
    for client in clients_sans_avocat:
        if sync_client_avocat_id(db, client.id):
            count += 1

    return count


def get_clients_export_data(db: Session, avocat_id: int) -> List[dict]:
    clients, _ = get_clients_by_avocat(db, avocat_id, skip=0, limit=10000)

    export_data = []
    for client in clients:
        stats = get_client_stats(db, client.id)

        demandeur = db.query(Demandeur).filter(
            Demandeur.client_id == client.id
        ).first()

        if not demandeur and client.dossiers:
            demandeur = db.query(Demandeur).filter(
                Demandeur.dossier_id == client.dossiers[0].id
            ).first()

        export_data.append({
            "id": client.id,
            "nom": demandeur.nom if demandeur and demandeur.nom else client.nom,
            "email": demandeur.email if demandeur and demandeur.email else client.email,
            "telephone": demandeur.telephone if demandeur and demandeur.telephone else client.telephone,
            "adresse": client.adresse or "N/A",
            "type": client.qualite or "N/A",
            "total_dossiers": stats.get("total_dossiers", 0),
            "statut": stats.get("statut", ""),
            "dossiers_actifs": stats.get("dossiers_actifs", 0)
        })

    return export_data