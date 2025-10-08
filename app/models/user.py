from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.core.enums import RoleEnum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.avocat, nullable=False)
    is_active = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    phone = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    created_by = relationship("User", remote_side=[id], backref="clerks")
    dossier = relationship("Dossier", back_populates="users")
    action_logs = relationship("ActionLog", back_populates="user")




