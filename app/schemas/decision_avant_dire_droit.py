from pydantic import BaseModel
from datetime import date
from typing import Optional


class DecisionAvantDireDroitBase(BaseModel):
    date_decision: date
    nature_incident: str
    contenu: Optional[str] = None


class DecisionAvantDireDroitCreate(DecisionAvantDireDroitBase):
    dossier_id: int


class DecisionAvantDireDroitUpdate(BaseModel):
    date_decision: Optional[date] = None
    nature_incident: Optional[str] = None
    contenu: Optional[str] = None


class DecisionAvantDireDroitOut(DecisionAvantDireDroitBase):
    id: int
    dossier_id: int
    ordonnance_file: Optional[str] = None

    class Config:
        orm_mode = True
