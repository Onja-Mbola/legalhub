from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.enums import RoleEnum

class UserCreate(BaseModel):
    nom: str
    email: EmailStr
    role: RoleEnum
    created_by_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    nom: str
    email: EmailStr
    role: RoleEnum

    class Config:
        orm_mode = True
