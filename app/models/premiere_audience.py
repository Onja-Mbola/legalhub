from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timedelta


class PremiereAudience(Base):
    __tablename__ = "premieres_audiences"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False)

    pv_audience = Column(String, nullable=True)
    decision = Column(String, nullable=False)
    nouvelle_date_audience = Column(DateTime, nullable=True)
    nom_judge = Column(String, nullable=True)
    observations_judge = Column(Text, nullable=True)
    observations_internes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow() + timedelta(hours=3),nullable=True)

    dossier = relationship("Dossier", back_populates="premieres_audiences")
