from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class AvantDireDroit(Base):
    __tablename__ = "avant_dire_droit"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    deliberation_decision_id = Column(Integer, ForeignKey("deliberations_decisions.id", ondelete="CASCADE"),
                                      nullable=False)

    date_decision_add = Column(Date, nullable=False)
    motif_renvoi = Column(Text, nullable=True)
    delai_conclusions = Column(Integer, nullable=True)
    date_limite_conclusions = Column(Date, nullable=True)

    copie_decision_add = Column(String, nullable=True)
    observations = Column(Text, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="decisions_add")
    deliberation_decision = relationship("DeliberationDecision", back_populates="decisions_add")
    nouveaux_echanges = relationship("EchangeConclusion", back_populates="decision_add", cascade="all, delete-orphan")
