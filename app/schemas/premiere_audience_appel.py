from pydantic import BaseModel
from typing import Optional
from datetime import date, time


class PremiereAudienceAppelBase(BaseModel):
    date_audience: date
    heure_audience: Optional[time] = None
    lieu_audience: Optional[str] = None
    juge_rapporteur: Optional[str] = None
    observations: Optional[str] = None


class PremiereAudienceAppelCreate(PremiereAudienceAppelBase):
    convocation_recue: Optional[str] = None
    enrolement_appel_id: int


class PremiereAudienceAppelUpdate(PremiereAudienceAppelBase):
    convocation_recue: Optional[str] = None


class PremiereAudienceAppelInDBBase(PremiereAudienceAppelBase):
    id: int
    dossier_id: int
    enrolement_appel_id: int
    convocation_recue: Optional[str] = None

    class Config:
        orm_mode = True


class PremiereAudienceAppel(PremiereAudienceAppelInDBBase):
    pass