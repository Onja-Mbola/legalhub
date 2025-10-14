from typing import Optional

from pydantic import BaseModel


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
