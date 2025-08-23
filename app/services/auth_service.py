import os
from datetime import timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.repositories.user import activate_user, get_user_by_email, create_user
from app.services.email import send_activation_email


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte inactif")
    return user


async def register_user_by_email(db, nom, email, role):
    if get_user_by_email(db, email):
        raise ValueError("Utilisateur déjà existant")
    user = create_user(db, nom, email, role, is_active=False)
    token = create_access_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    await send_activation_email(user.email, token)
    return user

def authenticate_user(email: str, password: str, db):
    user = get_user_by_email(db, email)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte inactif")
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")
    return user

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

def activate_account(db, token: str, default_password="123456"):
    email = decode_token(token)
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    activate_user(db, user, default_password)
    return user