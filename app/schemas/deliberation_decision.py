from pydantic import BaseModel
from datetime import date
from typing import Optional


class DeliberationDecisionBase(BaseModel):
    date_mise_en_delibere: date
    type_decision_attendue: str
    observations_juge: Optional[str] = None


class DeliberationDecisionCreate(DeliberationDecisionBase):
    dossier_id: int
    retour_audience_id: Optional[int] = None


class DeliberationDecisionUpdate(BaseModel):
    date_mise_en_delibere: Optional[date] = None
    type_decision_attendue: Optional[str] = None
    observations_juge: Optional[str] = None


class DeliberationDecisionOut(DeliberationDecisionBase):
    id: int
    dossier_id: int
    note_audience_file: Optional[str] = None

    class Config:
        orm_mode = True
