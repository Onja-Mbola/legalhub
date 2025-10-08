from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, validator


class OppositionBase(BaseModel):
    date_notification: date
    opposition_possible_jusqua: Optional[date] = None
    opposition_formulee: bool = False
    date_opposition: Optional[date] = None
    acte_opposition: Optional[str] = None
    motifs_opposition: Optional[str] = None
    alerte_envoyee: bool = False


class OppositionCreate(OppositionBase):
    dossier_id: int
    jugement_id: Optional[int] = None
    decision_fond_id: Optional[int] = None

    @validator('decision_fond_id', 'jugement_id')
    def check_ids(cls, v, values):

        jugement_id = values.get('jugement_id')
        decision_fond_id = v

        if jugement_id is None and decision_fond_id is None:
            raise ValueError("Au moins jugement_id ou decision_fond_id doit être fourni")

        return v


class OppositionUpdate(BaseModel):
    date_notification: Optional[date] = None
    opposition_possible_jusqua: Optional[date] = None
    opposition_formulee: Optional[bool] = None
    date_opposition: Optional[date] = None
    acte_opposition: Optional[str] = None
    motifs_opposition: Optional[str] = None
    alerte_envoyee: Optional[bool] = None

    @validator('date_opposition')
    def validate_date_opposition(cls, v, values):
        if v and values.get('date_notification'):
            if v < values['date_notification']:
                raise ValueError(
                    "La date d'opposition ne peut pas être antérieure à la date de notification"
                )
        return v

    class Config:
        orm_mode = True


class OppositionOut(OppositionBase):
    id: int
    dossier_id: int
    jugement_id: Optional[int] = None
    decision_fond_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True