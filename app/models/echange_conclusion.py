from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class EchangeConclusion(Base):
    __tablename__ = "echanges_conclusions"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    # Qui a déposé / déposé conjoint ?
    partie = Column(String, nullable=False)
    contenu_resume = Column(Text, nullable=True)
    motif_renvoi = Column(Text, nullable=True)

    date_depot = Column(Date, nullable=False)
    conclusions_file = Column(String, nullable=True)

    dossier = relationship("Dossier", back_populates="echanges_conclusions")
