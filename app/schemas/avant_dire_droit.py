from datetime import date
from typing import Optional
from pydantic import BaseModel, validator


class DecisionADDBase(BaseModel):
    date_decision_add: date
    motif_renvoi: Optional[str] = None
    delai_conclusions: Optional[int] = None
    copie_decision_add: Optional[str] = None
    observations: Optional[str] = None


class DecisionADDCreate(DecisionADDBase):
    dossier_id: int
    deliberation_decision_id: int

    @validator('delai_conclusions')
    def validate_delai(cls, v):
        if v is not None and v < 1:
            raise ValueError("Le délai doit être au moins 1 jour")
        return v


class DecisionADDUpdate(BaseModel):
    date_decision_add: Optional[date] = None
    motif_renvoi: Optional[str] = None
    delai_conclusions: Optional[int] = None
    date_limite_conclusions: Optional[date] = None
    copie_decision_add: Optional[str] = None
    observations: Optional[str] = None


class DecisionADDOut(DecisionADDBase):
    id: int
    dossier_id: int
    deliberation_decision_id: int
    date_limite_conclusions: Optional[date]
    alerte_envoyee: bool

    class Config:
        from_attributes = True