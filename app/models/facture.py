from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.facture_enum import StatutFacture, TypeRappel
from app.db.base_class import Base
from app.models.paiement import Paiement


class Facture(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, index=True)
    numero_facture = Column(String, unique=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    nom_client_anonyme = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    montant_ht = Column(Float, nullable=False)
    taux_tva = Column(Float, default=0.0)
    montant_ttc = Column(Float, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_emission = Column(DateTime, nullable=True)
    date_echeance = Column(DateTime, nullable=False)
    date_paiement = Column(DateTime, nullable=True)
    statut = Column(Enum(StatutFacture), default=StatutFacture.BROUILLON)
    rappel_active = Column(Boolean, default=False)
    type_rappel = Column(Enum(TypeRappel), default=TypeRappel.AUCUN)
    prochaine_relance = Column(DateTime, nullable=True)
    nombre_relances = Column(Integer, default=0)
    fichier_facture = Column(String, nullable=True)
    preuve_paiement = Column(String, nullable=True)
    notes_internes = Column(Text, nullable=True)
    facture_parent_id = Column(Integer, ForeignKey("factures.id"), nullable=True)

    dossier = relationship("Dossier", back_populates="factures")
    paiements = relationship('Paiement', back_populates="facture")
    facture_parent = relationship("Facture", remote_side=[id], backref="factures_enfant")

    def __repr__(self):
        return f"<Facture {self.numero_facture}: {self.montant_ttc}€ - {self.statut.value}>"

    @property
    def montant_paye(self) -> float:
        return sum(p.montant for p in self.paiements)

    @property
    def montant_restant(self) -> float:
        return max(self.montant_ttc - self.montant_paye, 0)

    @property
    def montant_total_avec_enfants(self) -> float:
        if self.facture_parent_id is None:
            return self.montant_ttc
        return self.montant_ttc

    @property
    def montant_paye_total_avec_enfants(self) -> float:
        if self.facture_parent_id is None:
            total = self.montant_paye
            for enfant in self.factures_enfant:
                total += enfant.montant_paye
            return total
        return self.montant_paye

    @property
    def montant_restant_global(self) -> float:
        if self.facture_parent_id is None:  # Seulement pour les factures parents
            return max(self.montant_ttc - self.montant_paye_total_avec_enfants, 0)
        elif self.facture_parent:
            return self.facture_parent.montant_restant_global
        return self.montant_restant

    @property
    def montant_restant_facture_mere(self) -> float:
        if self.facture_parent_id is None:
            total_factures_filles = sum(f.montant_ttc for f in self.factures_enfant)
            return max(self.montant_ttc - total_factures_filles - self.montant_paye, 0)
        return self.montant_restant

    @property
    def est_completement_payee(self) -> bool:
        if self.facture_parent_id is None:
            return self.montant_restant_global <= 0
        return self.montant_restant <= 0

    def get_facture_principale(self):
        if self.facture_parent_id is None:
            return self
        return self.facture_parent