from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.db.base_class import Base

def init_db():
    # Crée les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)

    # Insère 10 utilisateurs si la table est vide
    db: Session = SessionLocal()
    if db.query(User).count() == 0:
        users = [
            User(nom=f"Utilisateur{i}", email=f"user{i}@legalhub.fr", role="avocat")
            for i in range(1, 11)
        ]
        db.add_all(users)
        db.commit()
        print("✅ 10 utilisateurs ajoutés.")
    else:
        print("✅ La table 'users' contient déjà des données.")
    db.close()
