from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.profile import ProfileUpdate, PasswordChangeRequest, ClerkCreateForm
from app.services.user import update_user_profile
from app.utils.validators import validate_password_strength

router = APIRouter(prefix="/api/v1/profile", tags=["profile-api"])


@router.get("/me")
async def get_my_profile(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nom": current_user.nom,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "phone": getattr(current_user, 'phone', None),
        "created_at": current_user.created_at if hasattr(current_user, 'created_at') else None
    }


@router.put("/update")
async def update_profile_api(
        profile_data: ProfileUpdate,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        from app.repositories.user import check_email_exists
        if check_email_exists(db, profile_data.email, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé"
            )

        updated_user = update_user_profile(db, current_user.id, profile_data.dict())

        return {
            "message": "Profil mis à jour avec succès",
            "user": {
                "nom": updated_user.nom,
                "email": updated_user.email,
                "phone": getattr(updated_user, 'phone', None)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/password/validate")
async def validate_new_password(password_data: dict):
    password = password_data.get("password", "")
    validation = validate_password_strength(password)

    return {
        "is_valid": validation["is_valid"],
        "strength": validation["strength"],
        "score": validation["score"],
        "feedback": validation["feedback"]
    }