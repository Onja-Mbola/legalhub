import asyncio
import os
from datetime import timedelta

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.email import send_activation_email
from app.services.user import list_users
from app.core.enums import RoleEnum


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

@router.get("/admin/dashboard")
def dashboard_admin(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    users = list_users(db)
    return templates.TemplateResponse("admin/dashboard_admin.html", {
        "request": request,
        "user": user,
        "users": users
    })



@router.get("/admin/users/create", response_class=HTMLResponse)
def create_user_page(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    roles = list(RoleEnum)
    return templates.TemplateResponse("admin/admin_create_user.html", {
        "request": request,
        "user": current_user,
        "roles": roles
    })

@router.post("/admin/users/create", response_class=HTMLResponse)
async def user_create_submit(
    request: Request,
    nom: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("admin/admin_create_user.html", {
            "request": request,
            "user": current_user,
            "roles": list(RoleEnum),
            "error": "Un utilisateur avec cet email existe déjà."
        })
    try:
        user = User(
            nom=nom,
            email=email,
            role=role,
            is_active=False,
            created_by_id=current_user.id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(
            {"sub": user.email},
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        await send_activation_email(user.email, token)

        return RedirectResponse(url="/admin/dashboard", status_code=302)

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("admin/admin_create_user.html", {
            "request": request,
            "user": current_user,
            "roles": list(RoleEnum),
            "error": "Erreur lors de la création du compte."
        })

