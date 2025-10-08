from typing import Optional

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


def update_user_by_id(db: Session, user_id: int, updates: dict) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user


def check_email_exists(db: Session, email: str, exclude_user_id: int = None) -> bool:
    query = db.query(User).filter(User.email == email)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None


def get_users_by_creator(db: Session, creator_id: int):
    return db.query(User).filter(User.created_by_id == creator_id).all()
