from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.schemas.client import ClientBase


class DossierCreate(BaseModel):
    nom_dossier: str
    type_affaire: str
    sous_type_affaire: Optional[str]
    urgence: Optional[str]
    juridiction: Optional[str]
    tribunal: Optional[str]
    avocat_responsable: str
    avocat_adverse: Optional[str]
    date_creation: Optional[datetime]
    commentaire: Optional[str]
    client: Optional[ClientBase]


class DossierOut(DossierCreate):
    numero_dossier: str
    dossier_path: str
    pieces_jointes: Optional[List[str]]

    class Config:
        orm_mode = True
