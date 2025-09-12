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
    JUGEMENT_FAVORABLE = "jugement_favorable"
    JUGEMENT_DEFAVORABLE = "jugement_defavorable"
    FIN_ARCHIVAGE = "dossier_archivé"
    NOTIFICATION_CLIENT = "notification_client"
    RECUPERATION_GROSSE = "recuperation_grosse"
    JUGEMENT_CONTRADICTOIRE = "jugement_contradictoire"
    PAR_DEFAUT = "jugement_par_defaut"
    OPPOSITION = "opposition"
    RETOUR_AUDIENCE = "retour_audience"
    JUGEMENT_DEFINITIF= "jugement_definitif"
    ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT = "echange_conclusions_jugement_par_defaut"
    DELIBERATION_JUGEMENT_PAR_DEFAUT = "deliberation_jugement_par_defaut"
    NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT = "notification_client_jugement_par_defaut"


