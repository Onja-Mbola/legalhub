from http.client import HTTPException

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette import status

from app.core.auth import get_current_clerk_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/clerks/dashboard")
def dashboard_clerk(
    request: Request,
    user: User = Depends(get_current_clerk_user)
):

    events = [
        {"title": "Réunion", "start": "2025-07-10T10:00:00", "url": "#"},
        {"title": "Audience", "start": "2025-07-15", "allDay": True}
    ]
    return templates.TemplateResponse("clerk/dashboard_clerk.html", {
        "request": request,
        "user": user,
        "events": events
    })