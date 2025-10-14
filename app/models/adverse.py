from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Adverse(Base):
    __tablename__ = "adverses"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    nom = Column(String, nullable=False)
    qualite = Column(Integer, ForeignKey("param_general.id"), nullable=False)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    avocat = Column(String, nullable=True)

    dossier = relationship("Dossier", back_populates="adverses")
    qualite_param = relationship("ParamGeneral")