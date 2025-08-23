from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PremiereAudienceBase(BaseModel):
    decision: str
    nouvelle_date_audience: Optional[datetime] = None
    nom_judge: Optional[str] = None
    observations_judge: Optional[str] = None
    observations_internes: Optional[str] = None


class PremiereAudienceCreate(PremiereAudienceBase):
    pv_audience: Optional[str] = None


class PremiereAudienceUpdate(PremiereAudienceBase):
    pv_audience: Optional[str] = None


class PremiereAudienceOut(PremiereAudienceBase):
    id: int
    dossier_id: int
    pv_audience: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
