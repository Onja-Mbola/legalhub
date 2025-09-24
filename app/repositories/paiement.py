from sqlalchemy.orm import Session
from app.models.paiement import Paiement


class PaiementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, facture_id: int, montant: float, preuve_paiement: str = None) -> Paiement:
        paiement = Paiement(facture_id=facture_id, montant=montant, preuve_paiement=preuve_paiement)
        self.db.add(paiement)
        self.db.commit()
        self.db.refresh(paiement)
        return paiement

    def get_by_facture(self, facture_id: int):
        return self.db.query(Paiement).filter(Paiement.facture_id == facture_id).all()

    def get(self, paiement_id: int):
        return self.db.query(Paiement).filter(Paiement.id == paiement_id).first()

    def update(self, paiement: Paiement, montant: float = None, preuve_paiement: str = None) -> Paiement:
        if montant is not None:
            paiement.montant = montant
        if preuve_paiement is not None:
            paiement.preuve_paiement = preuve_paiement
        self.db.commit()
        self.db.refresh(paiement)
        return paiement

    def delete(self, paiement: Paiement) -> None:
        self.db.delete(paiement)
        self.db.commit()

