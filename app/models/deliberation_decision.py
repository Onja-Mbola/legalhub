from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models import jugement_definitif, retour_audience


class DeliberationDecision(Base):
    __tablename__ = "deliberations_decisions"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    retour_audience_id = Column(Integer, ForeignKey("retours_audiences.id", ondelete="CASCADE"), nullable=True)

    date_mise_en_delibere = Column(Date, nullable=False)
    type_decision_attendue = Column(String, nullable=False)
    note_audience_file = Column(String, nullable=True)
    observations_juge = Column(Text, nullable=True)

    dossier = relationship("Dossier", back_populates="deliberations_decisions")
    retour_audience = relationship("RetourAudience", back_populates="deliberations_decisions")
    jugements_definitifs = relationship("JugementDefinitif", back_populates="deliberation")

