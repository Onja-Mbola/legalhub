from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.client import ClientCreate
from app.schemas.demandeur import DemandeurCreate
from app.schemas.adverse import AdverseCreate


class DossierCreate(BaseModel):
    nom_dossier: str
    type_affaire: int
    sous_type_affaire: Optional[int] = None
    urgence: Optional[int] = None
    juridiction: Optional[str] = None
    tribunal: Optional[str] = None
    avocat_responsable: int
    date_creation: Optional[datetime] = None
    commentaire: Optional[str] = None
    consentement_rgpd: bool = False

    mode_creation: str = "nouveau"

    client_id: Optional[int] = None

    nouveau_client: Optional['ClientCreate'] = None

    demandeurs: List['DemandeurCreate'] = []
    adverses: List['AdverseCreate'] = []


class DossierOut(BaseModel):
    id: int
    numero_dossier: str
    nom_dossier: str
    type_affaire: int
    sous_type_affaire: Optional[int]
    urgence: Optional[int]
    current_stage: str
    client_id: Optional[int]
    dossier_path: Optional[str]
    pieces_jointes: Optional[List[str]]

    class Config:
        orm_mode = True


DossierCreate.update_forward_refs(
    ClientCreate=ClientCreate,
    DemandeurCreate=DemandeurCreate,
    AdverseCreate=AdverseCreate
)
