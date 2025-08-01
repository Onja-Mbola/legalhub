from fastapi import Depends, Request, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.enums import RoleEnum
from app.db.session import get_db
from app.models.user import User
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Email invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs.")
    return current_user

def get_current_avocat_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.avocat:
        raise HTTPException(status_code=403, detail="Accès réservé aux avocats.")
    return current_user

def get_current_clarck_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.clarck:
        raise HTTPException(status_code=403, detail="Accès réservé aux Clarck.")
    return current_user