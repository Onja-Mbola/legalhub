from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class OppositionBase(BaseModel):
    dossier_id: int
    jugement_id: int
    date_notification: date
    opposition_possible_jusqua: date

class OppositionCreate(OppositionBase):
    pass

class OppositionUpdate(BaseModel):
    date_notification: Optional[datetime] = None
    opposition_possible_jusqua: Optional[datetime] = None
    alerte_envoyee: Optional[bool] = None

class OppositionOut(OppositionBase):
    id: int
    alerte_envoyee: bool
    created_at: datetime

    class Config:
        orm_mode = True
