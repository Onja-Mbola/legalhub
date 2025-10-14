from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, or_
from app.models.client import Client
from app.models.dossier import Dossier
from app.models.demandeur import Demandeur


def get_clients_by_avocat(
        db: Session,
        avocat_id: int,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: str = "nom",
        order: str = "asc"
) -> tuple[List[Client], int]:
    query = db.query(Client).outerjoin(
        Dossier, Client.id == Dossier.client_id
    ).filter(
        or_(
            Client.avocat_id == avocat_id,
            Dossier.avocat_responsable == avocat_id
        )
    ).options(
        joinedload(Client.dossiers)
    ).distinct()

    if search:
        subquery_demandeurs = db.query(Demandeur.client_id).filter(
            or_(
                Demandeur.nom.ilike(f"%{search}%"),
                Demandeur.email.ilike(f"%{search}%"),
                Demandeur.telephone.ilike(f"%{search}%")
            )
        ).subquery()

        query = query.filter(
            or_(
                Client.nom.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
                Client.telephone.ilike(f"%{search}%"),
                Client.id.in_(subquery_demandeurs)
            )
        )

    total = query.count()

    if sort_by == "nom":
        order_func = asc if order == "asc" else desc
        query = query.order_by(order_func(Client.nom))
    elif sort_by == "dossiers":
        query = query.outerjoin(Client.dossiers).group_by(Client.id)
        order_func = asc if order == "asc" else desc
        query = query.order_by(order_func(func.count(Dossier.id)))

    clients = query.offset(skip).limit(limit).all()
    return clients, total


def get_client_by_id(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).options(
        joinedload(Client.dossiers),
    ).filter(Client.id == client_id).first()


def get_client_stats(db: Session, client_id: int) -> dict:
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        return {}

    total_dossiers = len(client.dossiers)
    dossiers_actifs = sum(1 for d in client.dossiers if d.current_stage not in ['archivé', 'cloturé'])
    dossiers_archives = total_dossiers - dossiers_actifs

    if total_dossiers > 10:
        statut = "gros_client"
    elif total_dossiers > 5:
        statut = "client_regulier"
    else:
        statut = "nouveau_client"

    return {
        "total_dossiers": total_dossiers,
        "dossiers_actifs": dossiers_actifs,
        "dossiers_archives": dossiers_archives,
        "statut": statut
    }


def get_demandeur_principal_by_client(db: Session, client_id: int) -> Optional[Demandeur]:
    return db.query(Demandeur).filter(
        Demandeur.client_id == client_id
    ).first()


def count_clients_by_avocat(db: Session, avocat_id: int) -> int:
    return db.query(Client).outerjoin(
        Dossier, Client.id == Dossier.client_id
    ).filter(
        or_(
            Client.avocat_id == avocat_id,
            Dossier.avocat_responsable == avocat_id
        )
    ).distinct().count()


def get_all_clients(db: Session, avocat_id: int) -> List[Client]:
    return db.query(Client).outerjoin(
        Dossier, Client.id == Dossier.client_id
    ).filter(
        or_(
            Client.avocat_id == avocat_id,
            Dossier.avocat_responsable == avocat_id
        )
    ).distinct().all()


def search_clients(db: Session, avocat_id: int, search_term: str) -> List[Client]:
    return db.query(Client).outerjoin(
        Dossier, Client.id == Dossier.client_id
    ).filter(
        or_(
            Client.avocat_id == avocat_id,
            Dossier.avocat_responsable == avocat_id
        ),
        Client.nom.ilike(f"%{search_term}%")
    ).distinct().limit(10).all()


def get_all_demandeurs_orphelins(db: Session, avocat_id: int) -> List[Demandeur]:
    return db.query(Demandeur).join(
        Dossier, Demandeur.dossier_id == Dossier.id
    ).filter(
        Dossier.avocat_responsable == avocat_id,
        Demandeur.client_id == None
    ).all()


def get_clients_with_demandeurs(db: Session, avocat_id: int) -> List[dict]:
    clients = get_all_clients(db, avocat_id)

    result = []
    for client in clients:
        demandeur = get_demandeur_principal_by_client(db, client.id)

        if not demandeur and client.dossiers:
            demandeur = db.query(Demandeur).filter(
                Demandeur.dossier_id == client.dossiers[0].id
            ).first()

        result.append({
            "client": client,
            "demandeur": demandeur
        })

    return result


def sync_client_avocat_id(db: Session, client_id: int) -> bool:
    client = get_client_by_id(db, client_id)

    if not client or client.avocat_id:
        return False

    if client.dossiers:
        avocat_counts = {}
        for dossier in client.dossiers:
            avocat_id = dossier.avocat_responsable
            avocat_counts[avocat_id] = avocat_counts.get(avocat_id, 0) + 1

        avocat_principal = max(avocat_counts, key=avocat_counts.get)
        client.avocat_id = avocat_principal
        db.commit()
        return True

    return False


def sync_all_clients_avocat_id(db: Session) -> int:
    clients_sans_avocat = db.query(Client).filter(
        Client.avocat_id == None
    ).all()

    count = 0
    for client in clients_sans_avocat:
        if sync_client_avocat_id(db, client.id):
            count += 1

    return count


def create_client_from_demandeur(db: Session, demandeur_id: int) -> Optional[Client]:
    demandeur = db.query(Demandeur).filter(
        Demandeur.id == demandeur_id
    ).first()

    if not demandeur or demandeur.client_id:
        return None

    client = Client(
        nom=demandeur.nom,
        email=demandeur.email,
        telephone=demandeur.telephone,
        adresse=demandeur.adresse,
        avocat_id=demandeur.dossier.avocat_responsable if demandeur.dossier else None
    )
    db.add(client)
    db.flush()

    demandeur.client_id = client.id
    db.commit()

    return client


def convert_all_orphelins_to_clients(db: Session, avocat_id: int) -> int:
    orphelins = get_all_demandeurs_orphelins(db, avocat_id)

    count = 0
    for demandeur in orphelins:
        if create_client_from_demandeur(db, demandeur.id):
            count += 1

    return count
