from datetime import date
from typing import Optional
from pydantic import BaseModel, validator


class DecisionFondBase(BaseModel):
    date_decision_fond: date
    type_decision_fond: str
    sens_decision: Optional[str] = None
    texte_decision: Optional[str] = None
    date_notification: Optional[date] = None
    delai_appel: int = 30
    date_limite_appel: Optional[date] = None
    observations: Optional[str] = None
    copie_decision_fond: Optional[str] = None
    alerte_envoyee: bool = False


class DecisionFondCreate(DecisionFondBase):
    dossier_id: int
    deliberation_decision_id: int

    @validator('type_decision_fond')
    def validate_type_decision(cls, v):
        allowed_types = ["par_defaut", "contradictoire"]
        if v not in allowed_types:
            raise ValueError(f"Le type de décision doit être: {', '.join(allowed_types)}")
        return v

    @validator('date_notification')
    def validate_notification_date(cls, v, values):
        if v and 'date_decision_fond' in values:
            if v < values['date_decision_fond']:
                raise ValueError(
                    "La date de notification ne peut pas être antérieure à la date de décision"
                )
        return v

    @validator('delai_appel')
    def validate_delai_appel(cls, v):
        if v < 0:
            raise ValueError("Le délai d'appel doit être positif")
        if v > 365:
            raise ValueError("Le délai d'appel ne peut pas dépasser 365 jours")
        return v


class DecisionFondUpdate(BaseModel):
    date_decision_fond: Optional[date] = None
    type_decision_fond: Optional[str] = None
    sens_decision: Optional[str] = None
    texte_decision: Optional[str] = None
    date_notification: Optional[date] = None
    delai_appel: Optional[int] = None
    date_limite_appel: Optional[date] = None
    observations: Optional[str] = None
    copie_decision_fond: Optional[str] = None
    alerte_envoyee: Optional[bool] = None

    @validator('type_decision_fond')
    def validate_type_decision(cls, v):
        if v is not None:
            allowed_types = ["par_defaut", "contradictoire"]
            if v not in allowed_types:
                raise ValueError(f"Le type de décision doit être: {', '.join(allowed_types)}")
        return v

    @validator('delai_appel')
    def validate_delai_appel(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Le délai d'appel doit être positif")
            if v > 365:
                raise ValueError("Le délai d'appel ne peut pas dépasser 365 jours")
        return v

    class Config:
        orm_mode = True


class DecisionFondOut(DecisionFondBase):
    id: int
    dossier_id: int
    deliberation_decision_id: int

    class Config:
        orm_mode = True