import enum


class StatutFacture(enum.Enum):
    BROUILLON = "brouillon"
    ENVOYEE = "envoyee"
    PAYEE = "payee"
    ANNULEE = "annulee"
    EN_RETARD = "en_retard"
    PARTIELLE = "partielle"

class TypeRappel(enum.Enum):
    HEBDOMADAIRE = "hebdomadaire"
    MENSUEL = "mensuel"
    FIN_MOIS = "fin_mois"
    AUCUN = "aucun"