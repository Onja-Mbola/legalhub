import os

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.auth import get_current_user, get_current_admin_user
from app.core.enums import RoleEnum
from app.db.session import get_db
from app.models.action_log import ActionLog
from app.models.user import User
from app.repositories.user import get_user_by_id
from app.schemas.user import UserCreate, UserOut
from app.services.action_log import get_log_service
from app.services.history import list_activation_history
from app.services.user import list_users, register_user, toggle_activation

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

@router.get("/admin/dashboard")
def dashboard_admin(
    request: Request,
    user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    users = list_users(db)
    return templates.TemplateResponse("admin/dashboard_admin.html", {
        "request": request,
        "user": user,
        "users": users
    })


@router.get("/admin/users/create", response_class=HTMLResponse)
def create_user_page(request: Request, current_user: User = Depends(get_current_admin_user)):
    roles = [RoleEnum.admin, RoleEnum.avocat]
    return templates.TemplateResponse("admin/admin_create_user.html", {
        "request": request,
        "user": current_user,
        "roles": roles
    })

@router.post("/admin/users/create", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_api(
    request: Request,
    nom: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin_user)
):
    try:
        await register_user(db, nom, email, role, current_user.id)
        return RedirectResponse(url="/admin/dashboard", status_code=303)


    except ValueError as e:
        return templates.TemplateResponse("admin/admin_create_user.html", {
            "request": request,
            "user": current_user,
            "roles": [RoleEnum.admin, RoleEnum.avocat],
            "error": str(e)
        })
    except Exception:
        db.rollback()
        return templates.TemplateResponse("admin/admin_create_user.html", {
            "request": request,
            "user": current_user,
            "roles": [RoleEnum.admin, RoleEnum.avocat],
            "error": "Erreur lors de la création du compte."
        })


@router.get("/admin/users/{user_id}/toggle")
async def toggle_user_activation(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if current_user.role == "avocat" and user.role != "clarck":
        raise HTTPException(status_code=403, detail="Un avocat ne peut gérer que ses clarcks")

    if current_user.role not in ["admin", "avocat"]:
        raise HTTPException(status_code=403, detail="Action non autorisée")

    await toggle_activation(db, user, current_user)

    return RedirectResponse(url="/admin/dashboard", status_code=302)


@router.get("/admin/history", response_class=HTMLResponse)
def view_history(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    history = list_activation_history(db)

    return templates.TemplateResponse("admin/history.html", {
        "request": request,
        "user": current_user,
        "history": history
    })

@router.get("/admin/action_logs")
def list_action_logs(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_admin_user)):
    logs = get_log_service(db)
    return templates.TemplateResponse("admin/historique.html", {
        "request": request,
        "user": user,
        "logs": logs
    })
