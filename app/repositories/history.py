from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, aliased

from app.models.activation_history import ActivationHistory
from app.models.user import User


def get_activation_history(db: Session):
    UserAlias = aliased(User)
    ActorAlias = aliased(User)

    history = (
        db.query(ActivationHistory, UserAlias, ActorAlias)
        .join(UserAlias, ActivationHistory.user)
        .join(ActorAlias, ActivationHistory.actor)
        .order_by(ActivationHistory.timestamp.desc())
        .all()
    )
    return history

def create_history_db(db: Session, user_id: int, actor_id: int, action: str):
    history = ActivationHistory(
        user_id=user_id,
        actor_id=actor_id,
        action=action,
        timestamp = datetime.utcnow() + timedelta(hours=3)
    )
    db.add(history)
    db.commit()
    db.refresh(history)
