import os
import json  # NOUVEAU : Pour JSON paths si DB String
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.models.jugement_definitif import JugementDefinitif
from app.models.dossier import Dossier
from app.repositories.jugement_definitif import (
    create_jugement_definitif,
    update_jugement_definitif,
    get_jugements_definitifs_by_dossier, get_jugement_definitif
)
from app.schemas.jugement_definitif import JugementDefinitifCreate, JugementDefinitifUpdate
from app.services.action_log import log_action_service
from app.services.dossier import get_dossier_by_id_service
from app.services.opposition_service import check_opposition_exists_for_dossier
from app.services.workflow_guard import WorkflowGuard
from app.services.upload_processor import process_upload
from app.services.FileStorageService import storage


def create_jugement_definitif_service(
        db: Session,
        dossier_id: int,
        avocat_nom: str,
        data: JugementDefinitifCreate,
        user_id: int,
        fichiers: Optional[List[UploadFile]] = None
):
    dossier = get_dossier_by_id_service(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    stages_autorises = [ProcessStage.FOND.value, ProcessStage.DELIBERATION_JUGEMENT_PAR_DEFAUT.value,
                        ProcessStage.CASSATION.value]

    if dossier.current_stage not in stages_autorises:
        raise HTTPException(
            status_code=400,
            detail="Le jugement définitif n'est accessible qu'après la délibération ou décision de Fond."
        )

    opposition = check_opposition_exists_for_dossier(db, dossier_id)

    if opposition:
        date_jugement = data.date_jugement

        if date_jugement <= opposition.opposition_possible_jusqua:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de créer un jugement définitif. Une opposition est possible jusqu'au {opposition.opposition_possible_jusqua}. "
                       f"Veuillez d'abord mettre à jour l'opposition (formulée ou non)."
            )

        if not opposition.opposition_formulee:
            raise HTTPException(
                status_code=400,
                detail=f"Une opposition existe pour ce dossier mais n'a pas été mise à jour. "
                       f"Veuillez confirmer si une opposition a été formulée ou non."
            )

    jugement = create_jugement_definitif(db, data)
    # jugement.fichiers_jugement = []
    db.commit()  # Commit initia
    db.refresh(jugement)

    has_fichiers = fichiers and any(f.filename for f in fichiers)
    if has_fichiers:
        dossier_path = f"dossiers/{dossier.numero_dossier}/jugementdefinitifs/definitif"
        new_paths = storage.save_uploaded_files(fichiers, dossier_path)
        jugement.fichiers_jugement = new_paths
        db.commit()
        db.refresh(jugement)

    if has_fichiers and fichiers[0].filename:
        process_upload(
            obj=jugement,
            files=[fichiers[0]],
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="definitif"
        )
    else:
        process_upload(
            obj=jugement,
            files=[],
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="contenu",
            run_ml=True,
            subfolder="definitif"
        )

    WorkflowGuard.advance(dossier, ProcessStage.JUGEMENT_DEFINITIF, db)

    log_action_service(
        db, user_id,
        "Création jugement définitif",
        f"Création du jugement définitif pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return jugement


def update_jugement_definitif_service(
        db: Session,
        jugement_id: int,
        avocat_nom: str,
        user_id: int,
        data: JugementDefinitifUpdate,
        fichiers: Optional[List[UploadFile]] = None
):
    existing = get_jugement_definitif(db, jugement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Jugement définitif introuvable")

    dossier = existing.dossier

    updated = update_jugement_definitif(db, existing, data)
    db.commit()
    db.refresh(updated)

    has_new_fichiers = fichiers and any(f.filename for f in fichiers)
    if has_new_fichiers:
        old_paths = updated.fichiers_jugement or []
        if isinstance(old_paths, str):
            old_paths = json.loads(old_paths)

        dossier_path = f"dossiers/{dossier.numero_dossier}/jugementdefinitifs/definitif"
        new_paths = storage.save_uploaded_files(fichiers, dossier_path)

        all_paths = old_paths + new_paths
        updated.fichiers_jugement = all_paths
        db.commit()
        db.refresh(updated)

    if has_new_fichiers and fichiers[0].filename:
        process_upload(
            obj=updated,
            files=[fichiers[0]],
            db=db,
            dossier=dossier,
            file_field=None,
            contenu_field="contenu",
            ocr_all_files=False,
            run_ml=True,
            subfolder="definitif"
        )

    log_action_service(
        db, user_id,
        "Mise à jour jugement définitif",
        f"Mise à jour du jugement définitif pour le dossier {dossier.numero_dossier}",
        dossier.id
    )

    return updated


def get_jugement_definitif_by_id_service(db: Session, jugement_id: int):
    jugement = get_jugement_definitif(db, jugement_id)
    if not jugement:
        raise HTTPException(status_code=404, detail="Jugement définitif non trouvé")
    return jugement


def get_jugements_definitifs_by_dossier_service(db: Session, dossier_id: int):
    return get_jugements_definitifs_by_dossier(db, dossier_id)
