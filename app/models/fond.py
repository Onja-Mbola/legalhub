from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Fond(Base):
    __tablename__ = "fond"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    deliberation_decision_id = Column(Integer, ForeignKey("deliberations_decisions.id", ondelete="CASCADE"),
                                      nullable=False)

    date_decision_fond = Column(Date, nullable=False)
    type_decision_fond = Column(String, nullable=False)

    sens_decision = Column(String, nullable=True)
    texte_decision = Column(Text, nullable=True)
    copie_decision_fond = Column(String, nullable=True)

    date_notification = Column(Date, nullable=True)
    delai_appel = Column(Integer, default=30)
    date_limite_appel = Column(Date, nullable=True)

    observations = Column(Text, nullable=True)
    alerte_envoyee = Column(Boolean, default=False)

    ocr_texte = Column(Text, nullable=True)
    entites_extraites = Column(JSON, nullable=True)

    dossier = relationship("Dossier", back_populates="decisions_fond")
    deliberation_decision = relationship("DeliberationDecision", back_populates="decisions_fond")

    oppositions = relationship("Opposition", back_populates="decision_fond", cascade="all, delete-orphan")
    jugements_definitifs = relationship("JugementDefinitif", back_populates="decision_fond",
                                        cascade="all, delete-orphan")
    cassations = relationship("Cassation", back_populates="decision_fond", cascade="all, delete-orphan")

