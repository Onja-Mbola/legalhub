from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    adresse_client = Column(String, nullable=True)
    role_client = Column(Integer, ForeignKey("param_general.id"), nullable=True)

    dossiers = relationship("Dossier", back_populates="client")

    demandeurs = relationship("Demandeur", back_populates="client", cascade="all, delete")
    adverses = relationship("Adverse", back_populates="client", cascade="all, delete")

    role_client_param = relationship("ParamGeneral")