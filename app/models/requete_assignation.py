from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class RequeteAssignation(Base):
    __tablename__ = "requete_assignation"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    assignation_file = Column(String, nullable=True)
    preuve_signification_file = Column(String, nullable=True)
    nom_huissier = Column(String, nullable=True)
    date_signification = Column(Date, nullable=True)
    date_audience = Column(Date, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="requete_assignation")


