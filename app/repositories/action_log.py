from app.models.action_log import ActionLog
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta


def log_action(db: Session, user_id: int, action_type: str, description: str, dossier_id: int = None):
    action = ActionLog(
        user_id=user_id,
        dossier_id=dossier_id,
        action_type=action_type,
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_log(db: Session):
    logs = (
        db.query(ActionLog)
        .join(ActionLog.user)
        .outerjoin(ActionLog.dossier)
        .options(
            joinedload(ActionLog.user),
            joinedload(ActionLog.dossier)
        )
        .order_by(ActionLog.created_at.desc())
        .all()
    )

    for log in logs:
        log.created_at = log.created_at + timedelta(hours=3)

    return logs
