from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PremiereAudienceAppel(Base):
    __tablename__ = "premieres_audiences_appel"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    enrolement_appel_id = Column(Integer, ForeignKey("enrolements.id", ondelete="CASCADE"), nullable=False)

    date_audience = Column(Date, nullable=False)
    heure_audience = Column(Time, nullable=True)
    lieu_audience = Column(String, nullable=True)
    juge_rapporteur = Column(String, nullable=True)

    convocation_recue = Column(String, nullable=True)
    observations = Column(Text, nullable=True)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="premieres_audiences_appel")
    enrolement_appel = relationship("Enrolement", foreign_keys=[enrolement_appel_id])
    echanges_conclusions = relationship("EchangeConclusion", back_populates="premiere_appel",
                                        cascade="all, delete-orphan")
    deliberations_decisions = relationship("DeliberationDecision", back_populates="premieres_audiences_appel",
                                           cascade="all, delete-orphan")
