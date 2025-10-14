from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, validator


class CassationBase(BaseModel):
    date_notification_decision: date
    date_depot_requete: Optional[date] = None
    date_depot_memoire_ampliatif: Optional[date] = None
    date_reception_memoire_defense: Optional[date] = None
    date_limite_reponse: Optional[date] = None
    date_delibere: Optional[date] = None
    statut: str = "en_attente_requete"
    observations: Optional[str] = None
    copie_requete: Optional[str] = None
    copie_memoire_ampliatif: Optional[str] = None
    copie_memoire_defense: Optional[str] = None
    copie_reponse: Optional[str] = None
    date_limite_cassation: Optional[date] = None


class CassationCreate(CassationBase):
    decision_fond_id: int
    dossier_id: int

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @validator("date_depot_requete")
    def check_requete(cls, v, values):
        notif = values.get("date_notification_decision")
        if v:
            if notif and v < notif:
                raise ValueError("La requête ne peut pas être déposée avant la notification de décision")
            if notif and v > notif + timedelta(days=60):
                raise ValueError("La requête doit être déposée dans les 2 mois suivant la notification")
        return v

    @validator("date_depot_memoire_ampliatif")
    def check_memoire_ampliatif(cls, v, values):
        requete = values.get("date_depot_requete")
        if v:
            if not requete:
                raise ValueError("Mémoire ampliatif impossible sans dépôt de requête")
            if v < requete:
                raise ValueError("Le mémoire ampliatif ne peut pas être avant la requête")
            if v > requete + timedelta(days=60):
                raise ValueError("Le mémoire ampliatif doit être déposé dans les 2 mois après la requête")
        return v

    @validator("date_reception_memoire_defense")
    def check_memoire_defense(cls, v, values):
        ampliatif = values.get("date_depot_memoire_ampliatif")
        if v:
            if not ampliatif:
                raise ValueError("Réception du mémoire de défense impossible sans mémoire ampliatif")
            if v < ampliatif:
                raise ValueError("Le mémoire de défense ne peut pas être reçu avant le mémoire ampliatif")
        return v

    @validator("date_limite_reponse")
    def check_limite_reponse(cls, v, values):
        defense = values.get("date_reception_memoire_defense")
        if v:
            if not defense:
                raise ValueError("Délai de réponse impossible sans réception du mémoire de défense")
            if v < defense:
                raise ValueError("La date limite de réponse ne peut pas être avant le mémoire de défense")
            if v > defense + timedelta(days=10):
                raise ValueError("Le délai de réponse doit être de 10 jours après réception du mémoire de défense")
        return v

    @validator("date_delibere")
    def check_delibere(cls, v, values):
        dates = [values.get("date_notification_decision"), values.get("date_depot_requete"),
                 values.get("date_depot_memoire_ampliatif"), values.get("date_reception_memoire_defense"),
                 values.get("date_limite_reponse")]
        last_date = max([d for d in dates if d is not None], default=None)
        if v and last_date and v < last_date:
            raise ValueError("La date de délibéré doit être après toutes les étapes précédentes")
        return v

    @validator('statut')
    def validate_statut(cls, v):
        if v is not None:
            allowed = ["en_attente_requete", "requete_deposee", "memoire_ampliatif_depose",
                       "memoire_defense_recu", "reponse_envoyee", "delibere"]
            if v not in allowed:
                raise ValueError(f"Le statut doit être parmi: {', '.join(allowed)}")
        return v


class CassationUpdate(CassationBase):
    date_notification_decision: Optional[date] = None
    date_depot_requete: Optional[date] = None
    date_depot_memoire_ampliatif: Optional[date] = None
    date_reception_memoire_defense: Optional[date] = None
    date_limite_reponse: Optional[date] = None
    date_limite_memoire_ampliatif: Optional[date] = None
    date_delibere: Optional[date] = None
    statut: Optional[str] = None
    observations: Optional[str] = None
    copie_requete: Optional[str] = None
    copie_memoire_ampliatif: Optional[str] = None
    copie_memoire_defense: Optional[str] = None
    copie_reponse: Optional[str] = None
    alerte_requete_envoyee: Optional[bool] = None
    alerte_memoire_ampliatif_envoyee: Optional[bool] = None

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @validator("date_depot_requete")
    def update_check_requete(cls, v, values):
        notif = values.get("date_notification_decision")
        if v:
            if notif and v < notif:
                raise ValueError("La requête ne peut pas être déposée avant la notification de décision")
            if notif and v > notif + timedelta(days=60):
                raise ValueError("La requête doit être déposée dans les 2 mois suivant la notification")
        return v

    @validator("date_depot_memoire_ampliatif")
    def update_check_memoire_ampliatif(cls, v, values):
        requete = values.get("date_depot_requete")
        if v:
            if not requete:
                raise ValueError("Mémoire ampliatif impossible sans dépôt de requête")
            if v < requete:
                raise ValueError("Le mémoire ampliatif ne peut pas être avant la requête")
            if v > requete + timedelta(days=60):
                raise ValueError("Le mémoire ampliatif doit être déposé dans les 2 mois après la requête")
        return v

    @validator("date_reception_memoire_defense")
    def update_check_memoire_defense(cls, v, values):
        ampliatif = values.get("date_depot_memoire_ampliatif")
        if v:
            if not ampliatif:
                raise ValueError("Réception du mémoire de défense impossible sans mémoire ampliatif")
            if v < ampliatif:
                raise ValueError("Le mémoire de défense ne peut pas être reçu avant le mémoire ampliatif")
        return v

    @validator("date_limite_reponse")
    def update_check_limite_reponse(cls, v, values):
        defense = values.get("date_reception_memoire_defense")
        if v:
            if not defense:
                raise ValueError("Délai de réponse impossible sans réception du mémoire de défense")
            if v < defense:
                raise ValueError("La date limite de réponse ne peut pas être avant le mémoire de défense")
            if v > defense + timedelta(days=10):
                raise ValueError("Le délai de réponse doit être de 10 jours après réception du mémoire de défense")
        return v

    @validator("date_delibere")
    def update_check_delibere(cls, v, values):
        dates = [values.get("date_notification_decision"), values.get("date_depot_requete"),
                 values.get("date_depot_memoire_ampliatif"), values.get("date_reception_memoire_defense"),
                 values.get("date_limite_reponse")]
        last_date = max([d for d in dates if d is not None], default=None)
        if v and last_date and v < last_date:
            raise ValueError("La date de délibéré doit être après toutes les étapes précédentes")
        return v

    @validator('statut')
    def validate_statut(cls, v):
        if v is not None:
            allowed = ["en_attente_requete", "requete_deposee", "memoire_ampliatif_depose",
                       "memoire_defense_recu", "reponse_envoyee", "delibere"]
            if v not in allowed:
                raise ValueError(f"Le statut doit être parmi: {', '.join(allowed)}")
        return v

    class Config:
        orm_mode = True


class CassationOut(CassationBase):
    id: int
    decision_fond_id: int
    dossier_id: int
    date_limite_cassation: date
    date_limite_memoire_ampliatif: Optional[date] = None
    alerte_requete_envoyee: bool
    alerte_memoire_ampliatif_envoyee: bool

    class Config:
        orm_mode = True
