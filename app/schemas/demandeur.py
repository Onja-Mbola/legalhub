from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class DemandeurBase(BaseModel):
    nom: str
    qualite: str
    telephone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True