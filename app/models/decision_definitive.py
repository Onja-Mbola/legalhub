from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DecisionDefinitive(Base):
    __tablename__ = "decisions_definitives"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)

    date_decision = Column(Date, nullable=False)
    type_decision = Column(String, nullable=False)
    motivation = Column(Text, nullable=True)
    jugement_file = Column(String, nullable=True)

    dossier = relationship("Dossier", back_populates="decisions_definitives")
