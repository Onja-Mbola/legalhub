from sqlalchemy.orm import Session
from app.models.action_log import ActionLog
from datetime import datetime


def log_profile_change(db: Session, user_id: int, field_name: str, old_value: str, new_value: str):
    audit_log = ActionLog(
        user_id=user_id,
        action_type="profile_update",
        description=f"Changed {field_name} from '{old_value}' to '{new_value}'",
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()


def log_password_change_request(db: Session, user_id: int):
    audit_log = ActionLog(
        user_id=user_id,
        action_type="password_change_request",
        description="User requested password change",
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()


def log_clarck_creation(db: Session, creator_id: int, clarck_email: str):
    audit_log = ActionLog(
        user_id=creator_id,
        action_type="clarck_creation",
        description=f"Created clarck account for {clarck_email}",
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
