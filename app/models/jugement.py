from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Jugement(Base):
    __tablename__ = "jugements"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    date_jugement = Column(Date, nullable=False)
    texte_decision = Column(Text, nullable=True)
    sous_type = Column(String, nullable=True)

    delai_appel = Column(Integer, nullable=True)
    execution_provisoire = Column(Boolean, default=False)
    statut = Column(String, default="en_attente_recours")

    fichier_jugement = Column(String, nullable=True)
    scans_grosse = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="jugements")
    oppositions = relationship("Opposition", back_populates="jugement", cascade="all, delete-orphan")
    retours_audiences = relationship("RetourAudience", back_populates="jugement", cascade="all, delete-orphan")
