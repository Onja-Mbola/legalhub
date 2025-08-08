from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base
class Enrolement(Base):
    __tablename__ = "enrolements"
    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, unique=True)
    numero_role = Column(String, nullable=False, unique=True)
    date_enrolement = Column(Date, nullable=False)
    preuve_enrolement = Column(String, nullable=True)
    frais_payes = Column(Float, nullable=True)
    greffier = Column(String, nullable=True)

    dossier = relationship("Dossier", back_populates="enrolement")