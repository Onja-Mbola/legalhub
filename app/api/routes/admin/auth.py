import os
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut
from app.services.action_log import log_action_service
from app.services.auth_service import authenticate_user, register_user_by_email, decode_token, activate_account, \
    authenticate_google_user, reset_password, verify_reset_token, request_password_reset
from app.services.user import get_user_by_email_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


@router.get("/", include_in_schema=False)
@router.get("/login", include_in_schema=False)
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
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "google_client_id": google_client_id
    })


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(email, password, db)

        log_action_service(
            db=db,
            user_id=user.id,
            action_type="LOGIN",
            description=f"Connexion réussie via email/password pour {user.email}",
            dossier_id=None
        )

    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": str(e),
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")
        })

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url=f"/{user.role.value}/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True,
                        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        samesite="Lax", secure=True)
    return response


@router.post("/auth/google", response_class=HTMLResponse)
def google_login(request: Request, credential: str = Form(...), db: Session = Depends(get_db)):
    try:

        user = authenticate_google_user(credential, db)

        log_action_service(
            db=db,
            user_id=user.id,
            action_type="LOGIN",
            description=f"Connexion réussie via Google pour {user.email}",
            dossier_id=None
        )

        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        response = RedirectResponse(url=f"/{user.role.value}/dashboard", status_code=302)
        response.set_cookie(key="access_token", value=access_token, httponly=True,
                            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                            samesite="Lax", secure=True)
        return response

    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": str(e),
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")
        })


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
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        try:
            email = decode_token(token)
            user = get_user_by_email_service(db, email)
            if user:
                log_action_service(
                    db=db,
                    user_id=user.id,
                    action_type="LOGOUT",
                    description=f"Déconnexion pour {user.email}",
                    dossier_id=None
                )
        except Exception:
            pass

    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response



@router.get("/forgot_password")
def show_forgot_password(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", {
        "request": request
    })


@router.post("/forgot_password")
async def submit_forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        result = await request_password_reset(db, email)
        return templates.TemplateResponse("auth/forgot_password.html", {
            "request": request,
            "success": "Si cet email existe dans notre système, un lien de réinitialisation vous a été envoyé."
        })
    except Exception as e:
        return templates.TemplateResponse("auth/forgot_password.html", {
            "request": request,
            "success": "Si cet email existe dans notre système, un lien de réinitialisation vous a été envoyé."
        })


@router.get("/reset_password")
def show_reset_password(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        verify_reset_token(db, token)
        return templates.TemplateResponse("auth/reset_password.html", {
            "request": request,
            "token": token
        })
    except HTTPException as e:
        return templates.TemplateResponse("auth/reset_password_error.html", {
            "request": request,
            "error": e.detail
        })


@router.post("/reset_password")
async def submit_reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        await reset_password(db, token, new_password, confirm_password)
        return templates.TemplateResponse("auth/reset_password_success.html", {
            "request": request
        })
    except HTTPException as e:
        return templates.TemplateResponse("auth/reset_password.html", {
            "request": request,
            "token": token,
            "error": e.detail
        })