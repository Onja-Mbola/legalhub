# app/routes/profile.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_avocat_user
from app.db.session import get_db
from app.services.user import update_user_profile, register_user, register_clerk
from app.core.security import verify_password, hash_password
from app.services.email import send_password_change_confirmation
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profil")
def show_profile(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user
    })


@router.post("/profil/update")
async def update_profile(
        request: Request,
        nom: str = Form(...),
        email: str = Form(...),
        phone: str = Form(None),
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        from app.repositories.user import get_user_by_email
        existing_user = get_user_by_email(db, email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

        updated_user = update_user_profile(db, current_user.id, {
            "nom": nom,
            "email": email,
            "phone": phone
        })

        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": updated_user,
            "success": "Profil mis à jour avec succès !"
        })

    except Exception as e:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": str(e)
        })


@router.post("/profil/password/request-change")
async def request_password_change_endpoint(
        request: Request,
        current_password: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...),
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        if not verify_password(current_password, current_user.password):
            raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Les mots de passe ne correspondent pas")

        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères")

        confirmation_token = secrets.token_urlsafe(32)

        from app.models.password_change_request import PasswordChangeRequest
        password_request = PasswordChangeRequest(
            user_id=current_user.id,
            new_password_hash=hash_password(new_password),
            confirmation_token=confirmation_token
        )
        db.add(password_request)
        db.commit()

        await send_password_change_confirmation(current_user.email, confirmation_token)

        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "success": "Un email de confirmation a été envoyé à votre adresse."
        })

    except Exception as e:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": str(e)
        })


@router.get("/confirm-password-change")
async def confirm_password_change(
        token: str,
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        from app.models.password_change_request import PasswordChangeRequest
        from app.repositories.user import get_user_by_id

        password_request = db.query(PasswordChangeRequest).filter(
            PasswordChangeRequest.confirmation_token == token,
            PasswordChangeRequest.is_used == False
        ).first()

        if not password_request:
            raise HTTPException(status_code=404, detail="Token invalide ou expiré")

        user = get_user_by_id(db, password_request.user_id)
        user.password = password_request.new_password_hash

        password_request.is_used = True

        db.commit()

        return templates.TemplateResponse("password/password_changed_success.html", {
            "request": request
        })

    except Exception as e:
        raise HTTPException(status_code=404, detail="Erreur lors de la confirmation du changement de mot de passe")


@router.post("/profil/create-clerk")
async def create_clerk(
        request: Request,
        clerk_nom: str = Form(...),
        clerk_email: str = Form(...),
        send_welcome_email: bool = Form(False),
        current_user=Depends(get_current_avocat_user),
        db: Session = Depends(get_db)
):
    try:
        if current_user.role != "avocat":
            raise HTTPException(status_code=403, detail="Seuls les avocats peuvent créer des comptes clerk")

        from app.repositories.user import get_user_by_email
        existing_user = get_user_by_email(db, clerk_email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà")

        new_clerk = await register_clerk(
            db=db,
            nom=clerk_nom,
            email=clerk_email,
            role="clerk",
            created_by_id=current_user.id
        )

        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "success": f"Compte clerk créé avec succès pour {clerk_nom} ! Un email d'activation a été envoyé."
        })

    except Exception as e:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": str(e)
        })
