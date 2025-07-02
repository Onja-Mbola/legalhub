from http.client import HTTPException

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette import status

from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/clarck/dashboard")
def dashboard_clarck(
    request: Request,
    user: User = Depends(get_current_user)
):
    if user.role != "clarck":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    events = [
        {"title": "Réunion", "start": "2025-07-10T10:00:00", "url": "#"},
        {"title": "Audience", "start": "2025-07-15", "allDay": True}
    ]
    return templates.TemplateResponse("clarck/dashboard_clarck.html", {
        "request": request,
        "user": user,
        "events": events
    })