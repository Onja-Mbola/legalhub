from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.core.security import verify_password

def authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte inactif")
    return user