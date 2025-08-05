import os
from datetime import timedelta

from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.activation_history import ActivationHistory
from app.models.user import User
from app.repositories.user import get_all_users, create_user, get_user_by_email, activate_user
from app.services.email import send_activation_email, send_activation
from app.services.history import create_history

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def list_users(db: Session):
    return get_all_users(db)

def get_user_by_email_service(db: Session, email: str) -> User | None:
    return get_user_by_email(db, email)

async def register_user(db, nom: str, email: str, role: str, created_by_id: int):
    if get_user_by_email(db, email):
        raise ValueError("Un utilisateur avec cet email existe déjà.")

    if role == "clarck":
        raise ValueError("L'admin ne peut pas créer de clarck. Seul un avocat peut le faire.")

    user = create_user(db, nom, email, role, created_by_id)

    token = create_access_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    await send_activation_email(user.email, token)

    return user


async def toggle_activation(db: Session, user: User, actor: User):
    user.is_active = not user.is_active
    action = "activation" if user.is_active else "desactivation"
    create_history(db,user_id=user.id, actor_id=actor.id, action=action)

    if user.is_active:
        await send_activation(user.email)



