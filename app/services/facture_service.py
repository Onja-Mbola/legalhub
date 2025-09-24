import asyncio
import os
import uuid
from datetime import date
from datetime import datetime
from typing import Optional, List

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.automatisation.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.facture import Facture, StatutFacture
from app.models.user import User
from app.repositories import facture as facture_repo
from app.repositories.dossier import get_dossier_by_id
from app.repositories.facture import get_factures_en_attente_relance, update_relance_facture, get_facture_by_id
from app.repositories.facture import get_statistiques_facturation, get_factures_by_avocat
from app.repositories.user import get_user_by_id
from app.schemas.facture import FactureCreate, FactureUpdate
from app.services.FileStorageService import save_uploaded_files
from app.services.email import send_email
from app.services.email import send_facture_email, send_relance_facture_email
from app.services.pdf_generator import generate_facture_pdf
from app.services.pdf_generator import generate_rapport_facturation_pdf


def create_facture_with_file(
        db: Session,
        facture_data: FactureCreate,
        avocat_id: int,
        avocat_nom: str
) -> Facture:
    dossier = get_dossier_by_id(db, facture_data.dossier_id)
    if not dossier or dossier.avocat_responsable != avocat_id:
        raise HTTPException(status_code=404, detail="Dossier non trouvé ou accès non autorisé")

    facture = facture_repo.create_facture(db, facture_data, avocat_id)

    try:
        facture.date_emission = datetime.utcnow()
        facture.statut = StatutFacture.ENVOYEE

        pdf_path = generate_and_save_facture_pdf(facture, dossier, avocat_nom)
        facture.fichier_facture = pdf_path

        db.commit()
        db.refresh(facture)

    except Exception as e:
        db.delete(facture)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}")

    return facture


def update_facture_with_files(
        db: Session,
        facture_id: int,
        facture_update: FactureUpdate,
        avocat_id: int,
        avocat_nom: str,
        preuve_paiement: Optional[UploadFile] = None
) -> Optional[Facture]:
    facture = facture_repo.get_facture_by_id(db, facture_id, avocat_id)
    if not facture:
        return None

    if preuve_paiement and preuve_paiement.filename:
        dossier = get_dossier_by_id(db, facture.dossier_id)
        file_path = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "factures", "preuves")

        try:
            saved_files = save_uploaded_files([preuve_paiement], file_path)
            facture_update.preuve_paiement = os.path.join(file_path, saved_files[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

    updated_facture = facture_repo.update_facture(db, facture_id, facture_update, avocat_id)

    if updated_facture:
        if updated_facture.montant_restant <= 0:
            updated_facture.statut = StatutFacture.PAYEE
            updated_facture.rappel_active = False
            updated_facture.prochaine_relance = None
        elif updated_facture.montant_paye > 0:
            updated_facture.statut = StatutFacture.PARTIELLE

        if updated_facture.facture_parent_id is None and updated_facture.factures_enfant:
            if updated_facture.est_completement_payee:
                updated_facture.statut = StatutFacture.PAYEE
                updated_facture.rappel_active = False
                updated_facture.prochaine_relance = None

                for enfant in updated_facture.factures_enfant:
                    if enfant.montant_restant <= 0:
                        enfant.statut = StatutFacture.PAYEE
                        enfant.rappel_active = False
                        enfant.prochaine_relance = None

        db.commit()

    return updated_facture


def generate_and_save_facture_pdf(facture: Facture, dossier, avocat_nom: str) -> str:
    facture_dir = os.path.join("app/documents", avocat_nom, dossier.numero_dossier, "factures")
    os.makedirs(facture_dir, exist_ok=True)

    filename = f"facture_{facture.numero_facture}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(facture_dir, filename)

    pdf_content = generate_facture_pdf(facture, dossier)

    with open(file_path, 'wb') as f:
        f.write(pdf_content)

    return file_path


@celery_app.task(name="send_facture_email_task")
def send_facture_email_task(email: str, facture_data: dict, pdf_path: str):
    try:
        # Ajout du montant restant dans les données de l'email
        asyncio.run(send_facture_email(email, facture_data, pdf_path))
        return {"status": "success", "message": "Email envoyé avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="send_relance_facture_task")
def send_relance_facture_task(email: str, facture_data: dict):
    try:
        asyncio.run(send_relance_facture_email(email, facture_data))
        return {"status": "success", "message": "Relance envoyée avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="check_and_send_relances")
def check_and_send_relances():
    db = SessionLocal()
    try:
        factures_relance = get_factures_en_attente_relance(db)

        for facture in factures_relance:
            client_email = facture.dossier.client.email if hasattr(facture.dossier, 'client') else None

            if client_email:
                facture_data = {
                    'numero_facture': facture.numero_facture,
                    'montant_ttc': facture.montant_ttc,
                    'montant_paye': facture.montant_paye,
                    'montant_restant': facture.montant_restant,
                    'date_echeance': facture.date_echeance.isoformat(),
                    'nom_client': facture.nom_client_anonyme,
                    'description': facture.description,
                    'nombre_relances': facture.nombre_relances
                }

                send_relance_facture_task.delay(client_email, facture_data)
                update_relance_facture(db, facture.id)

        return f"Traité {len(factures_relance)} relances"

    except Exception as e:
        return f"Erreur: {str(e)}"
    finally:
        db.close()


@celery_app.task(name="update_facture_status_task")
def update_facture_status_task():
    from app.db.session import SessionLocal
    from app.models.facture import Facture

    db = SessionLocal()
    try:
        today = date.today()

        factures_retard = db.query(Facture).filter(
            Facture.statut == StatutFacture.ENVOYEE,
            Facture.date_echeance < today
        ).all()

        count_updated = 0
        for facture in factures_retard:
            if facture.montant_restant > 0:
                facture.statut = StatutFacture.EN_RETARD
                count_updated += 1

        db.commit()

        return f"Mis à jour {count_updated} factures en retard"

    except Exception as e:
        db.rollback()
        return f"Erreur lors de la mise à jour des statuts: {str(e)}"
    finally:
        db.close()


@celery_app.task(name="generate_monthly_report")
def generate_monthly_report_task(avocat_id: int):
    db = SessionLocal()
    try:
        avocat = get_user_by_id(db, avocat_id)
        if not avocat:
            return {"status": "error", "message": "Avocat non trouvé"}

        stats = get_statistiques_facturation(db, avocat_id, datetime.now().year)
        factures = get_factures_by_avocat(db, avocat_id, 0, 1000)

        pdf_content = generate_rapport_facturation_pdf(factures, stats, avocat.nom)

        report_dir = os.path.join("app/documents", avocat.nom, "rapports")
        os.makedirs(report_dir, exist_ok=True)

        filename = f"rapport_facturation_{datetime.now().strftime('%Y_%m')}.pdf"
        file_path = os.path.join(report_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(pdf_content)

        email_content = f"""
        <h2>Rapport mensuel de facturation</h2>
        <p>Veuillez trouver ci-joint votre rapport mensuel de facturation.</p>
        <p><strong>Statistiques du mois:</strong></p>
        <ul>
            <li>Total facturé: {stats.total_facture:.2f} Ariary</li>
            <li>Total payé: {stats.total_paye:.2f} Ariary</li>
            <li>Montant restant: {stats.total_impaye:.2f} Ariary</li>
            <li>Taux de recouvrement: {stats.taux_recouvrement:.1f}%</li>
        </ul>
        """

        # Note: Cette partie nécessiterait d'adapter send_email pour les pièces jointes
        asyncio.run(send_email(avocat.email, "Rapport mensuel de facturation", email_content))

        return {
            "status": "success",
            "message": f"Rapport généré: {file_path}",
            "stats": {
                "total_facture": stats.total_facture,
                "total_paye": stats.total_paye,
                "total_restant": stats.total_impaye,
                "taux_recouvrement": stats.taux_recouvrement
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="cleanup_old_facture_files")
def cleanup_old_facture_files():
    import os
    from datetime import datetime, timedelta

    try:
        cutoff_date = datetime.now() - timedelta(days=730)
        documents_dir = "app/documents"

        if not os.path.exists(documents_dir):
            return "Répertoire documents inexistant"

        deleted_count = 0

        for avocat_dir in os.listdir(documents_dir):
            avocat_path = os.path.join(documents_dir, avocat_dir)
            if not os.path.isdir(avocat_path):
                continue

            for dossier_dir in os.listdir(avocat_path):
                dossier_path = os.path.join(avocat_path, dossier_dir)
                if not os.path.isdir(dossier_path):
                    continue

                factures_path = os.path.join(dossier_path, "factures")
                if os.path.exists(factures_path):
                    for file in os.listdir(factures_path):
                        file_path = os.path.join(factures_path, file)
                        if os.path.isfile(file_path):
                            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                            if file_time < cutoff_date:
                                os.remove(file_path)
                                deleted_count += 1

        return f"Supprimé {deleted_count} anciens fichiers de factures"

    except Exception as e:
        return f"Erreur lors du nettoyage: {str(e)}"


@celery_app.task(name="send_weekly_statistics")
def send_weekly_statistics_task():
    db = SessionLocal()
    try:
        avocats = db.query(User).filter(User.is_active == True).all()

        sent_count = 0

        for avocat in avocats:
            try:
                stats = get_statistiques_facturation(db, avocat.id)

                email_content = f"""
                <html>
                <body>
                    <h2>Statistiques hebdomadaires - Cabinet d'Avocat</h2>
                    <p>Bonjour Maître {avocat.nom},</p>

                    <p>Voici vos statistiques de facturation de la semaine:</p>

                    <div style="background-color: #f8f9fc; padding: 20px; border-radius: 5px;">
                        <h3>Résumé Financier</h3>
                        <ul>
                            <li><strong>Total facturé:</strong> {stats.total_facture:.2f} Ariary</li>
                            <li><strong>Total payé:</strong> {stats.total_paye:.2f} Ariary</li>
                            <li><strong>Montant restant:</strong> {stats.total_impaye:.2f} Ariary</li>
                            <li><strong>Taux de recouvrement:</strong> {stats.taux_recouvrement:.1f}%</li>
                        </ul>

                        <h3>Factures</h3>
                        <ul>
                            <li><strong>Total:</strong> {stats.nombre_factures_total}</li>
                            <li><strong>Payées:</strong> {stats.nombre_factures_payees}</li>
                            <li><strong>Partiellement payées:</strong> {stats.nombre_factures_partielles or 0}</li>
                            <li><strong>Impayées:</strong> {stats.nombre_factures_impayees}</li>
                        </ul>
                    </div>

                    <p>Connectez-vous à votre espace pour plus de détails.</p>

                    <p>Cordialement,<br>Votre système de gestion</p>
                </body>
                </html>
                """

                asyncio.run(send_email(
                    avocat.email,
                    "Statistiques hebdomadaires - Facturation",
                    email_content
                ))

                sent_count += 1

            except Exception as e:
                print(f"Erreur envoi stats pour {avocat.email}: {str(e)}")
                continue

        return f"Statistiques envoyées à {sent_count} avocats"

    except Exception as e:
        return f"Erreur générale: {str(e)}"
    finally:
        db.close()


def get_factures_by_avocat_service(
        db: Session,
        avocat_id: int,
        skip: int = 0,
        limit: int = 100
) -> List[Facture]:
    factures = get_factures_by_avocat(db, avocat_id, skip, limit)
    if not factures:
        raise HTTPException(status_code=404, detail="Aucune facture trouvée pour cet avocat")
    return factures


def get_facture_by_id_service(
        db: Session,
        facture_id: int,
        avocat_id: int
) -> Facture:
    facture = get_facture_by_id(db, facture_id, avocat_id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable pour cet avocat")
    return facture


def get_facture_statistics(db: Session, avocat_id: int, periode: str = "annee"):
    try:
        current_year = datetime.now().year

        if periode == "annee":
            stats = facture_repo.get_statistiques_facturation(db, avocat_id, current_year)
            if not hasattr(stats, 'recouvrement_par_mois'):
                stats.recouvrement_par_mois = {}
            return stats

        elif periode == "revenus":
            stats = facture_repo.get_statistiques_revenus(db, avocat_id, current_year)
            if stats is None:
                from app.schemas.facture import StatistiqueRevenu
                stats = StatistiqueRevenu(
                    revenus_par_mois={str(i): 0 for i in range(1, 13)},
                    revenus_par_type_affaire={},
                    evolution_mensuelle={}
                )
            return stats

        else:
            return facture_repo.get_statistiques_facturation(db, avocat_id)

    except Exception as e:
        print(f"Erreur get_facture_statistics({periode}): {e}")

        if periode == "revenus":
            from app.schemas.facture import StatistiqueRevenu
            return StatistiqueRevenu(
                revenus_par_mois={str(i): 0 for i in range(1, 13)},
                revenus_par_type_affaire={},
                evolution_mensuelle={}
            )
        else:
            from app.schemas.facture import StatistiqueFacturation
            return StatistiqueFacturation(
                total_facture=0,
                total_paye=0,
                total_impaye=0,
                nombre_factures_total=0,
                nombre_factures_payees=0,
                nombre_factures_impayees=0,
                taux_recouvrement=0,
                recouvrement_par_mois={}
            )


def get_complete_statistics(db: Session, avocat_id: int):
    try:
        if hasattr(facture_repo, 'get_statistiques_facturation_complete'):
            return facture_repo.get_statistiques_facturation_complete(db, avocat_id, datetime.now().year)

        stats_facturation = get_facture_statistics(db, avocat_id, "annee")
        stats_revenus = get_facture_statistics(db, avocat_id, "revenus")

        factures_en_retard = []
        top_clients = []
        delai_paiement_moyen = "N/A"

        if hasattr(facture_repo, 'get_factures_en_retard'):
            factures_en_retard = facture_repo.get_factures_en_retard(db, avocat_id)

        if hasattr(facture_repo, 'get_top_clients'):
            top_clients = facture_repo.get_top_clients(db, avocat_id, 5)

        if hasattr(facture_repo, 'get_delai_paiement_moyen'):
            delai_paiement_moyen = facture_repo.get_delai_paiement_moyen(db, avocat_id)

        return {
            'stats_facturation': stats_facturation,
            'stats_revenus': stats_revenus,
            'factures_en_retard': factures_en_retard,
            'top_clients': top_clients,
            'delai_paiement_moyen': delai_paiement_moyen
        }

    except Exception as e:
        print(f"Erreur get_complete_statistics: {e}")
        return None