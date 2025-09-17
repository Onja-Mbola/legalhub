from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RetourAudienceBase(BaseModel):
    dossier_id: int
    jugement_id: Optional[int] = None
    date_audience: datetime
    nom_judge: Optional[str] = None
    observations_judge: Optional[str] = None
    observations_internes: Optional[str] = None
    pv_audience: Optional[str] = None


class RetourAudienceCreate(RetourAudienceBase):
    pass


class RetourAudienceUpdate(BaseModel):
    date_audience: Optional[datetime] = None
    nom_judge: Optional[str] = None
    observations_judge: Optional[str] = None
    observations_internes: Optional[str] = None
    pv_audience: Optional[str] = None


class RetourAudienceOut(RetourAudienceBase):
    id: int
    pv_audience: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


