from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class JugementBase(BaseModel):
    dossier_id: int
    date_jugement: date
    texte_decision: Optional[str] = None
    sous_type: Optional[str] = None
    delai_appel: Optional[int] = None
    execution_provisoire: Optional[bool] = False
    statut: Optional[str] = "en_attente_recours"
    fichier_jugement: Optional[str] = None
    scans_grosse: Optional[List[str]] = None

class JugementCreate(JugementBase):
    pass

class JugementUpdate(BaseModel):
    texte_decision: Optional[str] = None
    sous_type: Optional[str] = None
    delai_appel: Optional[int] = None
    execution_provisoire: Optional[bool] = None
    statut: Optional[str] = None
    fichier_jugement: Optional[str] = None
    scans_grosse: Optional[List[str]] = None

class JugementOut(JugementBase):
    id: int

    class Config:
        orm_mode = True
