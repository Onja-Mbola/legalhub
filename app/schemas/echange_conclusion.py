from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class EchangeConclusionBase(BaseModel):
    partie: str
    date_depot: date
    contenu_resume: Optional[str] = None
    motif_renvoi: Optional[str] = None


class EchangeConclusionCreate(EchangeConclusionBase):
    dossier_id: int
    retour_audience_id: Optional[int] = None


class EchangeConclusionUpdate(BaseModel):
    partie: Optional[str] = None
    date_depot: Optional[date] = None
    contenu_resume: Optional[str] = None
    motif_renvoi: Optional[str] = None


class EchangeConclusionOut(EchangeConclusionBase):
    id: int
    dossier_id: int
    conclusions_file: Optional[List[str]]

    class Config:
        orm_mode = True
