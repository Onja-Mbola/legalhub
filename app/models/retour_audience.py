from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from app.models import jugement, deliberation_decision, echange_conclusion



class RetourAudience(Base):
    __tablename__ = "retours_audiences"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False)
    jugement_id = Column(Integer, ForeignKey("jugements.id", ondelete="CASCADE"), nullable=True)

    date_audience = Column(DateTime, nullable=False)
    nom_judge = Column(String, nullable=True)
    observations_judge = Column(Text, nullable=True)
    observations_internes = Column(Text, nullable=True)
    pv_audience = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    dossier = relationship("Dossier", back_populates="retours_audiences")
    jugement = relationship("Jugement", back_populates="retours_audiences")
    echanges_conclusions = relationship("EchangeConclusion", back_populates="retour_audience", cascade="all, delete-orphan")
    deliberations_decisions = relationship("DeliberationDecision", back_populates="retour_audience",
                                           cascade="all, delete-orphan")

