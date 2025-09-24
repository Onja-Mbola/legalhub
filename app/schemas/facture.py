from datetime import datetime, date
from typing import Optional, Dict
from pydantic import BaseModel, Field
from app.core.facture_enum import StatutFacture, TypeRappel


class FactureBase(BaseModel):
    nom_client_anonyme: str = Field(..., min_length=3, max_length=50)
    description: str = Field(..., min_length=3)
    montant_ht: float = Field(..., ge=0)
    taux_tva: float = Field(default=20.0, ge=0, le=100)
    date_echeance: date
    rappel_active: bool = Field(default=False)
    type_rappel: TypeRappel = Field(default=TypeRappel.AUCUN)
    notes_internes: Optional[str] = None
    facture_parent_id: Optional[int] = None


class FactureCreate(FactureBase):
    dossier_id: int

    class Config:
        from_attributes = True


class FactureUpdate(BaseModel):
    nom_client_anonyme: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=10)
    montant_ht: Optional[float] = Field(None, ge=0)
    taux_tva: Optional[float] = Field(None, ge=0, le=100)
    date_echeance: Optional[date] = None
    statut: Optional[StatutFacture] = None
    rappel_active: Optional[bool] = None
    type_rappel: Optional[TypeRappel] = None
    date_paiement: Optional[datetime] = None
    notes_internes: Optional[str] = None
    preuve_paiement: Optional[str] = None

    class Config:
        from_attributes = True


class FactureResponse(FactureBase):
    id: int
    numero_facture: str
    dossier_id: int
    montant_ttc: float
    date_creation: datetime
    date_emission: Optional[datetime]
    date_paiement: Optional[datetime]
    statut: StatutFacture
    prochaine_relance: Optional[datetime]
    nombre_relances: int
    fichier_facture: Optional[str]
    preuve_paiement: Optional[str]

    class Config:
        from_attributes = True


class FactureListResponse(BaseModel):
    id: int
    numero_facture: str
    nom_client_anonyme: str
    montant_ttc: float
    date_echeance: date
    statut: StatutFacture
    nombre_relances: int

    class Config:
        from_attributes = True


class StatistiqueFacturation(BaseModel):
    total_facture: float
    total_paye: float
    total_impaye: float
    nombre_factures_total: int
    nombre_factures_payees: int
    nombre_factures_impayees: int
    taux_recouvrement: float
    recouvrement_par_mois: Dict[str, float] = {}

    class Config:
        orm_mode = True


class StatistiqueRevenu(BaseModel):
    revenus_par_mois: dict
    revenus_par_type_affaire: dict
    evolution_mensuelle: dict