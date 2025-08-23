from pydantic import BaseModel
from typing import Optional
from datetime import date

class RequeteAssignationBase(BaseModel):
    nom_huissier: Optional[str] = None
    date_signification: Optional[date] = None
    date_audience: Optional[date] = None

class RequeteAssignationCreate(RequeteAssignationBase):
    pass

class RequeteAssignationUpdate(RequeteAssignationBase):
    pass

class RequeteAssignationOut(RequeteAssignationBase):
    id: int
    dossier_id: int
    assignation_file: Optional[str] = None
    preuve_signification_file: Optional[str] = None

    class Config:
        orm_mode = True
