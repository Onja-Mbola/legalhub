from sqlalchemy.orm import Session

from app.repositories.action_log import log_action, get_log


def log_action_service(db: Session, user_id: int, action_type: str, description: str, dossier_id: int | None):
    return log_action(db, user_id, action_type, description, dossier_id)


def get_log_service(db: Session):
    return get_log(db)
