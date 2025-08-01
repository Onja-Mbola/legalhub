from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class ParamGeneral(Base):
    __tablename__ = "param_general"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    valeur = Column(String, nullable=False)
    unite = Column(String, nullable=True)
    ordre = Column(Integer, nullable = False)
