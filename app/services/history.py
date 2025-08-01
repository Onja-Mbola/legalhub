from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.activation_history import ActivationHistory
from app.repositories.history import get_activation_history, create_history_db


def list_activation_history(db):
    return get_activation_history(db)


def create_history(db, user_id: int, actor_id: int, action: str):
    return create_history_db(db, user_id, actor_id, action)