from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship

from app.core.workflow_enums import ProcessStage
from app.db.base_class import Base
from app.models.action_log import ActionLog
from app.models.client import Client
from app.models.decision_avant_dire_droit import DecisionAvantDireDroit
from app.models.decision_definitive import DecisionDefinitive
from app.models.deliberation_decision import DeliberationDecision
from app.models.echange_conclusion import EchangeConclusion
from app.models.enrolement import Enrolement
from app.models.jugement import Jugement
from app.models.jugement_definitif import JugementDefinitif
from app.models.opposition import Opposition
from app.models.param_general import ParamGeneral
from app.models.premiere_audience import PremiereAudience
from app.models.requete_assignation import RequeteAssignation
from app.models.retour_audience import RetourAudience
from app.models.user import User


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
    client = relationship(lambda: Client, back_populates="dossiers")
    avocat_responsable_user = relationship(lambda: User, foreign_keys=[avocat_responsable])

    type_affaire_param = relationship(lambda: ParamGeneral, foreign_keys=[type_affaire])
    sous_type_affaire_param = relationship(lambda: ParamGeneral, foreign_keys=[sous_type_affaire])
    urgence_param = relationship(lambda: ParamGeneral, foreign_keys=[urgence])
    enrolement = relationship(lambda: Enrolement, back_populates="dossier", uselist=False)
    requete_assignation = relationship(lambda: RequeteAssignation, back_populates="dossier", uselist=False)
    premieres_audiences = relationship(lambda: PremiereAudience, back_populates="dossier", cascade="all, delete-orphan")
    echanges_conclusions = relationship(lambda: EchangeConclusion, back_populates="dossier", cascade="all, delete-orphan")
    deliberations_decisions = relationship(lambda: DeliberationDecision, back_populates="dossier", cascade="all, delete-orphan")
    decisions_avant_dire_droit = relationship(lambda: DecisionAvantDireDroit, back_populates="dossier", cascade="all, delete-orphan")
    decisions_definitives = relationship(lambda: DecisionDefinitive, back_populates="dossier", cascade="all, delete-orphan")
    jugements = relationship(lambda: Jugement, back_populates="dossier", cascade="all, delete-orphan")
    users = relationship(lambda: User, back_populates="dossier")
    action_logs = relationship(lambda: ActionLog, back_populates="dossier")
    oppositions = relationship(lambda: Opposition, back_populates="dossier", cascade="all, delete-orphan")
    retours_audiences = relationship(lambda: RetourAudience, back_populates="dossier", cascade="all, delete-orphan")
    jugements_definitifs = relationship(lambda: JugementDefinitif, back_populates="dossier", cascade="all, delete-orphan")
