from sqlalchemy import Column, Integer, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Opposition(Base):
    __tablename__ = "oppositions"

    id = Column(Integer, primary_key=True, index=True)
    jugement_id = Column(Integer, ForeignKey("jugements.id", ondelete="CASCADE"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False)

    date_notification = Column(Date, nullable=False)
    opposition_possible_jusqua = Column(Date, nullable=False)
    alerte_envoyee = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    jugement = relationship("Jugement", back_populates="oppositions")
    dossier = relationship("Dossier", back_populates="oppositions")
