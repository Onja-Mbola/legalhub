from pydantic import BaseModel
from typing import List, Optional

from app.schemas.adverse import AdverseBase
from app.schemas.demandeur import DemandeurBase


class ClientBase(BaseModel):
    adresse_client: Optional[str] = None
    role_client: Optional[int] = None
    demandeurs: Optional[List[DemandeurBase]] = None
    adverses: Optional[List[AdverseBase]] = None

    class Config:
        orm_mode = True
