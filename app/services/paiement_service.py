import os
from typing import List, Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.facture_enum import StatutFacture
from app.repositories.paiement import PaiementRepository
from app.services.FileStorageService import save_uploaded_files
from app.repositories.facture import get_facture_by_id, update_facture

from app.schemas.facture import FactureUpdate


def update_facture_parent_status(db: Session, facture, user_id: int):
    if facture.facture_parent_id:
        facture_principale = facture.get_facture_principale()
        if facture_principale:
            if facture_principale.est_completement_payee:
                statut_parent = StatutFacture.PAYEE
            elif facture_principale.montant_restant_global < facture_principale.montant_ttc:
                statut_parent = StatutFacture.PARTIELLE
            else:
                statut_parent = StatutFacture.BROUILLON

            update_facture(db, facture_principale.id, FactureUpdate(statut=statut_parent), user_id)


def add_paiement_service(
    db: Session,
    facture_id: int,
    user_id: int,
    montant: float,
    avocat_nom: str,
    fichiers: Optional[List[UploadFile]] = None
):
    facture = get_facture_by_id(db, facture_id, user_id)
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    montant_restant = max(facture.montant_ttc - (facture.montant_paye or 0), 0)
    if montant_restant <= 0:
        raise HTTPException(status_code=400, detail="La facture est déjà entièrement payée")

    base_path = os.path.join("app/documents", avocat_nom, facture.dossier.numero_dossier, "paiements")
    fichiers_paths = []

    if fichiers and any(f.filename.strip() for f in fichiers):
        saved_files = save_uploaded_files(fichiers, base_path)
        fichiers_paths = [os.path.join(base_path, f) for f in saved_files]

    paiement_repo = PaiementRepository(db)
    paiement = paiement_repo.create(
        facture_id=facture.id,
        montant=montant,
        preuve_paiement=fichiers_paths[0] if fichiers_paths else None
    )

    if facture.montant_paye >= facture.montant_ttc:
        statut = StatutFacture.PAYEE
    elif facture.montant_paye > 0:
        statut = StatutFacture.PARTIELLE
    else:
        statut = StatutFacture.BROUILLON

    facture_update = FactureUpdate(statut=statut)
    update_facture(db, facture.id, facture_update, user_id)

    update_facture_parent_status(db, facture, user_id)

    return paiement


def get_paiements_by_facture_service(db: Session, facture_id: int):
    paiement_repo = PaiementRepository(db)
    return paiement_repo.get_by_facture(facture_id)


def update_paiement_service(
    db: Session,
    paiement_id: int,
    montant: Optional[float] = None,
    fichiers: Optional[List[UploadFile]] = None,
    avocat_nom: Optional[str] = None
):
    paiement_repo = PaiementRepository(db)
    paiement = paiement_repo.get(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")

    fichiers_paths = []
    if fichiers and avocat_nom and any(f.filename.strip() for f in fichiers):
        base_path = os.path.join("app/documents", avocat_nom, paiement.facture.dossier.numero_dossier, "paiements")
        saved_files = save_uploaded_files(fichiers, base_path)
        fichiers_paths = [os.path.join(base_path, f) for f in saved_files]

    paiement = paiement_repo.update(
        paiement,
        montant=montant,
        preuve_paiement=fichiers_paths[0] if fichiers_paths else None
    )

    facture = paiement.facture

    if facture.montant_paye >= facture.montant_ttc:
        statut = StatutFacture.PAYEE
    elif facture.montant_paye > 0:
        statut = StatutFacture.PARTIELLE
    else:
        statut = StatutFacture.BROUILLON

    facture_update = FactureUpdate(statut=statut)
    update_facture(db, facture.id, facture_update, facture.dossier.avocat_responsable)

    update_facture_parent_status(db, facture, facture.dossier.avocat_responsable)

    return paiement


def delete_paiement_service(db: Session, paiement_id: int):
    paiement_repo = PaiementRepository(db)
    paiement = paiement_repo.get(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement introuvable")

    facture = paiement.facture
    paiement_repo.delete(paiement)

    if facture.montant_paye >= facture.montant_ttc:
        statut = StatutFacture.PAYEE
    elif facture.montant_paye > 0:
        statut = StatutFacture.PARTIELLE
    else:
        statut = StatutFacture.BROUILLON

    facture_update = FactureUpdate(statut=statut)
    update_facture(db, facture.id, facture_update, facture.dossier.avocat_responsable)

    update_facture_parent_status(db, facture, facture.dossier.avocat_responsable)

    return {"message": "Paiement supprimé avec succès"}
