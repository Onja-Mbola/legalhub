import os
import asyncio
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import hash_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import authenticate_user
from app.services.email import send_activation_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


@router.get("/", include_in_schema=False)
def root(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/login_Page", status_code=status.HTTP_302_FOUND)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
    except JWTError:
        return RedirectResponse("/login_Page", status_code=status.HTTP_302_FOUND)

    if role:
        return RedirectResponse(f"/{role}/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/login_Page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(email, password, db)
    except HTTPException as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": e.detail
        })

    if user.role not in ["admin", "avocat", "clarck"]:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Rôle inconnu"
        })

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(
        url=f"/{user.role.value}/dashboard",
        status_code=302
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="Lax",
        secure=False
    )

    return response

@router.post("/users/", response_model=UserOut)
async def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = User(
        nom=user_in.nom,
        email=user_in.email,
        role=user_in.role,
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    await send_activation_email(user.email, token)

    return user

@router.get("/activate")
def activate_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.is_active = True
    user.password = hash_password("123456")
    db.commit()

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
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response
