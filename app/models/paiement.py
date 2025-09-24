from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Paiement(Base):
    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=False)
    montant = Column(Float, nullable=False)
    date_paiement = Column(DateTime, default=datetime.utcnow)
    preuve_paiement = Column(String, nullable=True)

    facture = relationship("Facture", back_populates="paiements")

