from sqlalchemy.orm import Session
from app.models.user import User

def get_all_users(db: Session):
    return db.query(User).all()

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, nom: str, email: str, role: str, created_by_id: int) -> User:
    user = User(nom=nom, email=email, role=role, is_active=False, created_by_id=created_by_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
def activate_user(db: Session, user: User, default_password: str):
    from app.core.security import hash_password
    user.is_active = True
    user.password = hash_password(default_password)
    db.commit()