# api/auth.py
import os
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.core.auth import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import authenticate_user, register_user_by_email, decode_token, activate_account
from app.services.user import get_user_by_email_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

@router.get("/", include_in_schema=False)
def root(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login_Page")

    try:
        email = decode_token(token)
        user = get_user_by_email_service(db, email)
        if not user:
            return RedirectResponse("/login_Page")
    except Exception:
        return RedirectResponse("/login_Page")

    return RedirectResponse(f"/{user.role.value}/dashboard")


@router.get("/login_Page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(email, password, db)
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": e.detail})

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url=f"/{user.role.value}/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True,
                        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        samesite="Lax", secure=False)
    return response

@router.post("/users/", response_model=UserOut)
async def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = await register_user_by_email(db, user_in.nom, user_in.email, user_in.role)
    return user


@router.get("/activate", response_class=HTMLResponse)
def activate_user(token: str, db: Session = Depends(get_db)):
    user = activate_account(db, token)

    message = f"Compte activé pour {user.email}"
    html_content = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="3;url=/login_Page" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
            body {{
                background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
                height: 100vh;
                margin: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: 'Montserrat', sans-serif;
                color: white;
                text-align: center;
            }}
            h3 {{
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                text-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            p {{
                font-size: 1.2rem;
                margin-bottom: 2rem;
                opacity: 0.85;
            }}
            .loader {{
                border: 6px solid rgba(255, 255, 255, 0.3);
                border-top: 6px solid white;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <h3>{message}</h3>
        <p>Redirection vers la page de connexion...</p>
        <div class="loader"></div>
        <p style="margin-top: 1rem;"><a href="/login_Page" style="color: white;">Cliquez ici si la redirection ne fonctionne pas</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response
