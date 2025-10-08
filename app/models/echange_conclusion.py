from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models import retour_audience

class EchangeConclusion(Base):
    __tablename__ = "echanges_conclusions"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    retour_audience_id = Column(Integer, ForeignKey("retours_audiences.id", ondelete="CASCADE"), nullable=True)
    premiere_appel_id = Column(Integer, ForeignKey("premieres_audiences_appel.id", ondelete="CASCADE"), nullable=True)
    decision_add_id = Column(Integer, ForeignKey("avant_dire_droit.id", ondelete="CASCADE"), nullable=True)

    # Qui a déposé / déposé conjoint ?
    partie = Column(String, nullable=False)
    contenu_resume = Column(Text, nullable=True)
    motif_renvoi = Column(Text, nullable=True)

    date_depot = Column(Date, nullable=False)
    conclusions_file = Column(JSON, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="echanges_conclusions")
    retour_audience = relationship("RetourAudience", back_populates="echanges_conclusions")
    premiere_appel = relationship("PremiereAudienceAppel", back_populates="echanges_conclusions")

    decision_add = relationship("AvantDireDroit", back_populates="nouveaux_echanges")

