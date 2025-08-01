from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
<<<<<<< Updated upstream
    role = Column(String, default="avocat")
=======
    password = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.avocat, nullable=False)
    is_active = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_by = relationship("User", remote_side=[id], backref="clarcks")

>>>>>>> Stashed changes
