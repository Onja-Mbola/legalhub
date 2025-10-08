import os
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token, hash_password
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.repositories.user import activate_user, get_user_by_email, create_user
from app.repositories.user import get_user_by_id
from app.services.email import send_activation_email, send_password_reset_email

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


def authenticate_google_user(credential: str, db: Session):
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")

        idinfo = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            google_client_id
        )

        email = idinfo.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email non trouvé dans le token Google")

        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Aucun compte trouvé avec cette adresse email. Contactez l'administrateur."
            )

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")

        return user

    except ValueError as e:
        raise HTTPException(status_code=401, detail="Token Google invalide")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'authentification Google: {str(e)}")


async def request_password_reset(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte inactif")

    reset_token = secrets.token_urlsafe(32)

    db.query(PasswordResetRequest).filter(
        PasswordResetRequest.user_id == user.id,
        PasswordResetRequest.is_used == False
    ).update({"is_used": True})

    reset_request = PasswordResetRequest(
        user_id=user.id,
        reset_token=reset_token
    )
    db.add(reset_request)
    db.commit()

    await send_password_reset_email(user.email, reset_token, user.nom)

    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}


def verify_reset_token(db: Session, token: str):

    reset_request = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.reset_token == token,
        PasswordResetRequest.is_used == False
    ).first()

    if not reset_request:
        raise HTTPException(status_code=404, detail="Token invalide ou expiré")

    expiration_time = reset_request.created_at + timedelta(hours=24)
    if datetime.utcnow() > expiration_time:
        raise HTTPException(status_code=404, detail="Token expiré")

    return reset_request


async def reset_password(db: Session, token: str, new_password: str, confirm_password: str):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Les mots de passe ne correspondent pas")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères")

    reset_request = verify_reset_token(db, token)

    user = get_user_by_id(db, reset_request.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.password = hash_password(new_password)

    reset_request.is_used = True

    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}