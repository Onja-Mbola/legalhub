from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re


class ProfileUpdate(BaseModel):
    nom: str
    email: EmailStr
    phone: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$', v):
            raise ValueError('Format de téléphone invalide')
        return v


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v


class ClerkCreateForm(BaseModel):
    clerk_nom: str
    clerk_email: EmailStr
    send_welcome_email: bool = True
