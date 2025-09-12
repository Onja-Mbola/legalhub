from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


class JugementDefinitifBase(BaseModel):
    dossier_id: int
    deliberation_id: Optional[int] = None
    date_jugement: date
    texte_jugement: Optional[str] = None
    jugement_file: Optional[List[str]] = None
    observations: Optional[str] = None


class JugementDefinitifCreate(JugementDefinitifBase):
    pass


class JugementDefinitifUpdate(BaseModel):
    texte_jugement: Optional[str] = None
    jugement_file: Optional[str] = None
    observations: Optional[str] = None


class JugementDefinitifOut(JugementDefinitifBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
