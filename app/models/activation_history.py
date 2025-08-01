from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from app.models.user import User


class ActivationHistory(Base):
    __tablename__ = "activation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship(User, foreign_keys=[user_id])
    actor = relationship(User, foreign_keys=[actor_id])
