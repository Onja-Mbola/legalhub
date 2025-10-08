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
    ECHANGE_CONCLUSIONS_JUGEMENT_PAR_DEFAUT = "echange_conclusion"
    DELIBERATION_JUGEMENT_PAR_DEFAUT = "deliberations"
    NOTIFICATION_CLIENT_JUGEMENT_PAR_DEFAUT = "notification_clients"
    APPEL = "appel"
    ENROLEMENT_APPEL = "enrolement_appel"
    PREMIERE_AUDIENCE_APPEL = "premiere_audience_appel"
    ECHANGE_CONCLUSIONS_APPEL = "echange_conclusions_appel"
    DELIBERATION_APPEL = "deliberation_appel"
    AVANT_DIRE_DROIT = "avant_dire_droit"
    FOND = "fond"
    CASSATION = "cassation"



