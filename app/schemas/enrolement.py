from datetime import date
from typing import Optional

from pydantic import BaseModel


class EnrolementBase(BaseModel):
    numero_role: str
    date_enrolement: date
    frais_payes: Optional[float] = None
    greffier: Optional[str] = None


class EnrolementCreate(EnrolementBase):
    preuve_enrolement: Optional[str] = None
    jugement_id: Optional[int] = None


class EnrolementUpdate(EnrolementBase):
    preuve_enrolement: Optional[str] = None


class EnrolementInDBBase(EnrolementBase):
    id: int
    dossier_id: int
    preuve_enrolement: Optional[str] = None

    class Config:
        orm_mode = True


class Enrolement(EnrolementInDBBase):
    pass
