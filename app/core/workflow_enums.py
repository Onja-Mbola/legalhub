from enum import Enum


class ProcessStage(str, Enum):
    INTRODUCTION_INSTANCE = "introduction_instance"
    ENROLEMENT = "enrolement"
    REQUETE_ASSIGNATION = "requete_assignation"
    PREMIERE_AUDIENCE = "premiere_audience"
    ECHANGE_CONCLUSIONS = "echange_conclusions"
    DELIBERATION = "deliberation"
    DECISION_AVANT_DIRE_DROIT = "decision_avant_dire_droit"
    DECISION_DEFINITIVE = "decision_definitive"
