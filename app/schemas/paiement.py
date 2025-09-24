from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PaiementBase(BaseModel):
    montant: float = Field(..., gt=0, description="Montant payé")
    date_paiement: Optional[datetime] = None
    preuve_paiement: Optional[str] = None

class PaiementCreate(PaiementBase):
    pass

class PaiementRead(PaiementBase):
    id: int
    facture_id: int

    class Config:
        orm_mode = True
