from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.schemas.adverse import AdverseBase
from app.schemas.demandeur import DemandeurBase


class ClientBase(BaseModel):
    nom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    qualite: Optional[str] = None
    avocat_id: Optional[int] = None


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int

    class Config:
        orm_mode = True
