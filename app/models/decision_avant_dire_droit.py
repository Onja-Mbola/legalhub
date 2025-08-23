from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DecisionAvantDireDroit(Base):
    __tablename__ = "decisions_avant_dire_droit"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    date_decision = Column(Date, nullable=False)
    nature_incident = Column(String, nullable=False)
    contenu = Column(Text, nullable=True)
    ordonnance_file = Column(String, nullable=True)    

    dossier = relationship("Dossier", back_populates="decisions_avant_dire_droit")
