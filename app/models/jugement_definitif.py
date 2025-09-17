from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from app.models import deliberation_decision


class JugementDefinitif(Base):
    __tablename__ = "jugements_definitifs"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False)
    deliberation_id = Column(Integer, ForeignKey("deliberations_decisions.id", ondelete="CASCADE"), nullable=True)

    date_jugement = Column(Date, nullable=False)
    texte_jugement = Column(Text, nullable=True)
    jugement_file = Column(JSON, nullable=True)
    observations = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    dossier = relationship("Dossier", back_populates="jugements_definitifs")
    deliberation = relationship("DeliberationDecision", back_populates="jugements_definitifs")
