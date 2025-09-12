from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship

from app.core.workflow_enums import ProcessStage
from app.db.base_class import Base
from app.models import opposition,jugement_definitif



class Dossier(Base):
    __tablename__ = "dossiers"

    id = Column(Integer, primary_key=True, index=True)
    numero_dossier = Column(String, unique=True, index=True)
    nom_dossier = Column(String, nullable=False)

    type_affaire = Column(Integer, ForeignKey("param_general.id"), nullable=False)
    sous_type_affaire = Column(Integer, ForeignKey("param_general.id"), nullable=True)
    urgence = Column(Integer, ForeignKey("param_general.id"), nullable=True)

    juridiction = Column(String, nullable=True)
    tribunal = Column(String, nullable=True)
    avocat_responsable = Column(Integer, ForeignKey("users.id"), nullable=False)
    avocat_adverse = Column(String, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow() + timedelta(hours=3), nullable=True)
    commentaire = Column(Text, nullable=True)
    dossier_path = Column(String, nullable=True)
    pieces_jointes = Column(JSON, nullable=True)
    current_stage = Column(String, default=ProcessStage.INTRODUCTION_INSTANCE.value, nullable=False)
    last_completed_stage = Column(String, nullable=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="dossiers")

    type_affaire_param = relationship("ParamGeneral", foreign_keys=[type_affaire])
    sous_type_affaire_param = relationship("ParamGeneral", foreign_keys=[sous_type_affaire])
    urgence_param = relationship("ParamGeneral", foreign_keys=[urgence])
    enrolement = relationship("Enrolement", back_populates="dossier", uselist=False)
    requete_assignation = relationship("RequeteAssignation", back_populates="dossier", uselist=False)
    premieres_audiences = relationship("PremiereAudience", back_populates="dossier", cascade="all, delete-orphan")
    echanges_conclusions = relationship("EchangeConclusion", back_populates="dossier", cascade="all, delete-orphan")
    deliberations_decisions = relationship("DeliberationDecision", back_populates="dossier",
                                           cascade="all, delete-orphan")
    decisions_avant_dire_droit = relationship("DecisionAvantDireDroit", back_populates="dossier",
                                              cascade="all, delete-orphan")
    decisions_definitives = relationship("DecisionDefinitive", back_populates="dossier", cascade="all, delete-orphan")
    jugements = relationship("Jugement", back_populates="dossier", cascade="all, delete-orphan")
    jugements_defavorables = relationship("JugementDefavorable", back_populates="dossier", cascade="all, delete-orphan")
    users = relationship("User", back_populates="dossier")
    action_logs = relationship("ActionLog", back_populates="dossier")
    oppositions = relationship("Opposition", back_populates="dossier", cascade="all, delete-orphan")
    retours_audiences = relationship("RetourAudience", back_populates="dossier", cascade="all, delete-orphan")
    jugements_definitifs = relationship("JugementDefinitif", back_populates="dossier", cascade="all, delete-orphan")


