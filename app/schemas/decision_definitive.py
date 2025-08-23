from pydantic import BaseModel
from datetime import date
from typing import Optional


class DecisionDefinitiveBase(BaseModel):
    date_decision: date
    type_decision: str
    motivation: Optional[str] = None


class DecisionDefinitiveCreate(DecisionDefinitiveBase):
    dossier_id: int


class DecisionDefinitiveUpdate(BaseModel):
    date_decision: Optional[date] = None
    type_decision: Optional[str] = None
    motivation: Optional[str] = None


class DecisionDefinitiveOut(DecisionDefinitiveBase):
    id: int
    dossier_id: int
    jugement_file: Optional[str] = None

    class Config:
        orm_mode = True
