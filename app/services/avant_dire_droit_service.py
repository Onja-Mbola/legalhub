from datetime import timedelta
from typing import List, Type, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.avant_dire_droit import AvantDireDroit
from app.models.dossier import Dossier
from app.repositories.avant_dire_droit import (
    get_decision_add_by_id,
    create_decision_add,
    update_decision_add,
    delete_decision_add,
    get_decisions_add_by_dossier,
    get_decisions_add_by_deliberation,
    get_all_decisions_add_with_alerts_pending
)
from app.repositories.dossier import get_dossier_by_id
from app.schemas.avant_dire_droit import DecisionADDCreate, DecisionADDUpdate
from app.services.action_log import log_action_service
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload


def create_decision_add_service(
        db: Session,
        data: DecisionADDCreate,
        user_id: int,
        copie_decision_add: Optional[UploadFile] = None
) -> AvantDireDroit:
    dossier = get_dossier_by_id(db, data.dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.DELIBERATION_APPEL.value:
        raise HTTPException(
            status_code=400,
            detail="La décision avant dire droit n'est accessible qu'après la délibération."
        )

    date_limite = None
    if data.delai_conclusions:
        date_limite = data.date_decision_add + timedelta(days=data.delai_conclusions)

    decision_data = data.dict()
    decision_data['date_limite_conclusions'] = date_limite
    decision_add_create = DecisionADDCreate(**decision_data)

    decision = create_decision_add(db, decision_add_create)
    db.commit()
    db.refresh(decision)

    has_file = copie_decision_add and copie_decision_add.filename
    if has_file:
        process_upload(
            obj=decision,
            files=[copie_decision_add],
            db=db,
            dossier=dossier,
            file_field="copie_decision_add",
            contenu_field="observations",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_add"
        )
    else:
        process_upload(
            obj=decision,
            files=[],
            db=db,
            dossier=dossier,
            file_field="copie_decision_add",
            contenu_field="observations",
            run_ml=True,
            subfolder="decision_add"
        )

    next_stage = ProcessStage.AVANT_DIRE_DROIT
    WorkflowGuard.advance(dossier, next_stage, db)

    log_action_service(
        db, user_id,
        "Création avant dire droit",
        f"Création avant dire droit pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return decision


def get_decision_add_service(db: Session, decision_id: int) -> AvantDireDroit:
    decision = get_decision_add_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision ADD non trouvée")

    return decision


def get_decisions_by_dossier_service(db: Session, dossier_id: int) -> List[AvantDireDroit]:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    return get_decisions_add_by_dossier(db, dossier_id)


def get_decisions_by_deliberation_service(db: Session, deliberation_id: int) -> List[AvantDireDroit]:
    decisions = get_decisions_add_by_deliberation(db, deliberation_id)
    if not decisions:
        raise HTTPException(
            status_code=404,
            detail="Aucune décision ADD trouvée pour cette délibération"
        )

    return decisions


def update_decision_add_service(
        db: Session,
        decision_id: int,
        data: DecisionADDUpdate,
        user_id: int,
        copie_decision_add: Optional[UploadFile] = None
) -> AvantDireDroit:
    decision = get_decision_add_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision ADD non trouvée")

    dossier = get_dossier_by_id(db, decision.dossier_id)

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if data.date_decision_add or data.delai_conclusions:
        date_decision = data.date_decision_add or decision.date_decision_add
        delai = data.delai_conclusions or decision.delai_conclusions

        if delai:
            data.date_limite_conclusions = date_decision + timedelta(days=delai)

    updated_decision = update_decision_add(db, decision_id, data)
    db.commit()
    db.refresh(updated_decision)

    has_new_file = copie_decision_add and copie_decision_add.filename
    if has_new_file:
        process_upload(
            obj=updated_decision,
            files=[copie_decision_add],
            db=db,
            dossier=dossier,
            file_field="copie_decision_add",
            contenu_field="observations",
            ocr_all_files=False,
            run_ml=True,
            subfolder="decision_add"
        )

    log_action_service(
        db, user_id,
        "Mise à jour avant dire droit",
        f"Mise à jour avant dire droit pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return updated_decision


def delete_decision_add_service(db: Session, decision_id: int) -> dict:
    decision = get_decision_add_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision ADD non trouvée")

    dossier = get_dossier_by_id(db, decision.dossier_id)
    if dossier and dossier.current_stage != ProcessStage.AVANT_DIRE_DROIT.value:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer une décision ADD si le dossier n'est plus à cette étape"
        )

    if decision.copie_decision_add:
        from app.services.FileStorageService import storage
        try:
            storage.delete_object(decision.copie_decision_add)
            print(f"Fichier supprimé pour décision ADD {decision_id}: {decision.copie_decision_add}")
        except Exception as e:
            print(f"Erreur suppression fichier ADD {decision_id}: {str(e)}")

    success = delete_decision_add(db, decision_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de la décision ADD"
        )

    return {"message": "Décision ADD supprimée avec succès", "id": decision_id}


def get_pending_alerts_service(db: Session) -> list[Type[AvantDireDroit]]:
    decisions = get_all_decisions_add_with_alerts_pending(db)

    return decisions


def mark_alert_as_sent_service(db: Session, decision_id: int) -> AvantDireDroit:
    decision = get_decision_add_by_id(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision ADD non trouvée")

    update_data = DecisionADDUpdate(alerte_envoyee=True)
    updated_decision = update_decision_add(db, decision_id, update_data)

    return updated_decision
