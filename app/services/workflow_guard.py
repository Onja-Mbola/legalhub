from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.dossier import Dossier
from app.core.workflow_enums import ProcessStage

class WorkflowGuard:
    @staticmethod
    def ensure_can_go_to(stage: ProcessStage, dossier: Dossier):
        current = ProcessStage(dossier.current_stage)

        allowed = {
            ProcessStage.INTRODUCTION_INSTANCE: [ProcessStage.ENROLEMENT],
            ProcessStage.ENROLEMENT: [ProcessStage.REQUETE_ASSIGNATION],
            ProcessStage.REQUETE_ASSIGNATION: [ProcessStage.PREMIERE_AUDIENCE],
            ProcessStage.PREMIERE_AUDIENCE: [ProcessStage.ECHANGE_CONCLUSIONS],
            ProcessStage.ECHANGE_CONCLUSIONS: [ProcessStage.DELIBERATION],
            ProcessStage.DELIBERATION: [
                ProcessStage.DECISION_AVANT_DIRE_DROIT,
                ProcessStage.DECISION_DEFINITIVE
            ],
            ProcessStage.DECISION_AVANT_DIRE_DROIT: [ProcessStage.ECHANGE_CONCLUSIONS],
            ProcessStage.DECISION_DEFINITIVE: [],
        }

        if stage not in allowed[current]:
            raise HTTPException(
                status_code=400,
                detail=f"Transition interdite: {current.value} -> {stage.value}"
            )

    @staticmethod
    def advance(dossier: Dossier, new_stage: ProcessStage, db: Session):
        if not dossier.current_stage:
            dossier.current_stage = new_stage.value
            dossier.last_completed_stage = None
        else:
            WorkflowGuard.ensure_can_go_to(new_stage, dossier)
            dossier.last_completed_stage = dossier.current_stage
            dossier.current_stage = new_stage.value

        db.commit()
        db.refresh(dossier)
        return dossier



