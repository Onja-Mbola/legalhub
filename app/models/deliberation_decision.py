from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Deliberation_Decision(Base):
    __tablename__ = "deliberations_decisions"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    date_mise_en_delibere = Column(Date, nullable=False)
    type_decision_attendue = Column(String, nullable=False)
    note_audience_file = Column(String, nullable=True)  
    observations_juge = Column(Text, nullable=True)

    dossier = relationship("Dossier", back_populates="deliberations_decisions")
