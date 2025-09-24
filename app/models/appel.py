from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime


class Appel(Base):
    __tablename__ = "appels"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    motif = Column(String, nullable=True)

    date_depot = Column(DateTime, nullable=False, default=datetime.utcnow)
    statut = Column(String, default="en_attente")

    dossier = relationship("Dossier", back_populates="appels")
