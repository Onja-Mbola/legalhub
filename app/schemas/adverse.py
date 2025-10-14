from typing import Optional
from pydantic import BaseModel, EmailStr


class AdverseBase(BaseModel):
    nom: str
    qualite: int
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    avocat: Optional[str] = None


class AdverseCreate(AdverseBase):
    pass


class AdverseOut(AdverseBase):
    id: int
    dossier_id: int

    class Config:
        orm_mode = True
