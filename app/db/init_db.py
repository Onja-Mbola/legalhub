import time
from sqlalchemy.exc import OperationalError
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.db.base_class import Base
from app.core.security import hash_password
from sqlalchemy.orm import Session

def init_db(retries=5, delay=3):
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)

            db: Session = SessionLocal()
            if db.query(User).count() == 0:
                admin = User(
                    nom="Admin",
                    email="admin@legalhub.fr",
                    password=hash_password("admin123"),
                    role="admin",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                print("Admin initial créé")
            db.close()
            break
        except OperationalError as e:
            print(f" Erreur de connexion à la DB (tentative {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"Attente de {delay} secondes avant nouvelle tentative...")
                time.sleep(delay)
            else:
                print("Échec de connexion à la base de données après plusieurs tentatives.")
                raise
