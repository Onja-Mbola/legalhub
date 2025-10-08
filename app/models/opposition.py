from sqlalchemy import Column, Integer, Date, ForeignKey, Boolean, DateTime, String, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Opposition(Base):
    __tablename__ = "oppositions"

    id = Column(Integer, primary_key=True, index=True)
    jugement_id = Column(Integer, ForeignKey("jugements.id", ondelete="CASCADE"), nullable=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False)
    decision_fond_id = Column(Integer, ForeignKey("fond.id", ondelete="CASCADE"), nullable=True)

    date_notification = Column(Date, nullable=False)
    opposition_possible_jusqua = Column(Date, nullable=False)
    alerte_envoyee = Column(Boolean, default=False)
    opposition_formulee = Column(Boolean, default=False)
    date_opposition = Column(Date, nullable=True)

    acte_opposition = Column(String, nullable=True)
    motifs_opposition = Column(Text, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    jugement = relationship("Jugement", back_populates="oppositions")
    dossier = relationship("Dossier", back_populates="oppositions")
    decision_fond = relationship("Fond", back_populates="oppositions")

