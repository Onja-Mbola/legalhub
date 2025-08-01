from datetime import datetime

from sqlalchemy import Column, Enum, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.enums import TypeDeCas
from app.db.base_class import Base
from app.models.clients import Client


class Type(Base):
    __tablename__ = "type"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(TypeDeCas), nullable=False)
    description = Column(String, nullable=False)
    date_consultation = Column(DateTime, default=datetime.utcnow)

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    client = relationship(Client, back_populates="type")
