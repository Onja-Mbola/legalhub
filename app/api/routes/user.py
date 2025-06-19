from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user import list_users

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/utilisateurs")
def show_users(request: Request, db: Session = Depends(get_db)):
    users = list_users(db)
    return templates.TemplateResponse("utilisateurs.html", {"request": request, "users": users})
