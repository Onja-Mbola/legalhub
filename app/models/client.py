from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    qualite = Column(Integer, ForeignKey("param_general.id"), nullable=False)
    avocat_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    dossiers = relationship("Dossier", back_populates="client")
