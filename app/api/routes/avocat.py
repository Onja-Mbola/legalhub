
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette import status

from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/avocat/dashboard")
def dashboard_avocat(
    request: Request,
    user: User = Depends(get_current_user)
):
    if user.role != "avocat":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    return templates.TemplateResponse("avocat/dashboard_avocat.html", {
        "request": request,
        "user": user
    })