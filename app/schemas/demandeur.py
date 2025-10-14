from typing import Optional
from pydantic import BaseModel, EmailStr


class DemandeurBase(BaseModel):
    client_id: Optional[int] = None

    nom: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None

    qualite: int


class DemandeurCreate(DemandeurBase):
    pass


class DemandeurOut(DemandeurBase):
    id: int
    dossier_id: int

    class Config:
        orm_mode = True
