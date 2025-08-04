from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
class Demandeur(Base):
    __tablename__ = "demandeurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    qualite = Column(Integer, ForeignKey("param_general.id"), nullable=False)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="demandeurs")

    qualite_param = relationship("ParamGeneral")