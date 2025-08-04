from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

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
    date_creation = Column(Date, nullable=True)
    commentaire = Column(Text, nullable=True)
    dossier_path = Column(String, nullable=True)
    pieces_jointes = Column(JSON, nullable=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="dossiers")

    type_affaire_param = relationship("ParamGeneral", foreign_keys=[type_affaire])
    sous_type_affaire_param = relationship("ParamGeneral", foreign_keys=[sous_type_affaire])
    urgence_param = relationship("ParamGeneral", foreign_keys=[urgence])
