from sqlalchemy.orm import Session
from app.repositories.user import get_all_users

def list_users(db: Session):
    return get_all_users(db)
