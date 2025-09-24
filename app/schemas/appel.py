from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class AppelBase(BaseModel):
    dossier_id: int
    motif: Optional[str]
    statut: Optional[str] = "en_attente"
    date_depot: datetime


class AppelCreate(AppelBase):
    pass


class AppelUpdate(BaseModel):
    motif: Optional[str]
    statut: Optional[str]
    date_depot: datetime


class AppelOut(AppelBase):
    id: int
    motif: Optional[str]
    date_depot: datetime

    class Config:
        orm_mode = True
