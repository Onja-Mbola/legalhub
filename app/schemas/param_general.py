from pydantic import BaseModel
from typing import Optional

class ParamGeneralBase(BaseModel):
    nom: str
    valeur: str
    unite: Optional[str] = None
    ordre: Optional[str] = None

class ParamGeneralCreate(ParamGeneralBase):
    pass

class ParamGeneralUpdate(ParamGeneralBase):
    pass

class ParamGeneral(BaseModel):
    id: int
    nom: str
    valeur: str
    unite: Optional[str] = None
    ordre: Optional[str] = None

    class Config:
        orm_mode = True
