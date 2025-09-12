from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class JugementDefavorable(Base):
    __tablename__ = "jugements_defavorables"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    sous_type = Column(String, nullable=True)
    date_jugement = Column(Date, nullable=False)
    texte_decision = Column(String, nullable=True)
    jugement_file = Column(String, nullable=True)
    scan_grosse = Column(JSON, nullable=True)
    statut = Column(String, default="EN_COURS")

    dossier = relationship("Dossier", back_populates="jugements_defavorables")
    oppositions = relationship("Opposition", back_populates="jugement", cascade="all, delete-orphan")
    retours_audiences = relationship("RetourAudience", back_populates="jugement", cascade="all, delete-orphan")


