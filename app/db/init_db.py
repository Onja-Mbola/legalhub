import time
from sqlalchemy.exc import OperationalError
from app.db.session import engine, SessionLocal
from app.models import action_log, activation_history
from app.models.user import User
from app.models.param_general import ParamGeneral
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

            # Paramètres à créer
            params_to_create = [
                {"nom": "type_affaire", "valeur": "consultation", "unite": None, "ordre": 5},
                {"nom": "type_affaire", "valeur": "civil", "unite": None, "ordre": 10},
                {"nom": "type_affaire", "valeur": "penal", "unite": None, "ordre": 15},
                {"nom": "urgence", "valeur": "Tribunal de référé (7 ou 15 jours)", "unite": None, "ordre": 5},
                {"nom": "urgence", "valeur": "Tribunal de fond (1 mois ou 15 jours)", "unite": None, "ordre": 10},
                {"nom": "urgence", "valeur": "Tribunal de référé à bref délai", "unite": None, "ordre": 15},
                {"nom": "sous_type_civil", "valeur": "Commercial", "unite": None, "ordre": 5},
                {"nom": "sous_type_civil", "valeur": "Social", "unite": None, "ordre": 10},
                {"nom": "sous_type_civil", "valeur": "Sous-section 1 a 9", "unite": None, "ordre": 15},
                {"nom": "sous_type_penal", "valeur": "Correctionnel", "unite": None, "ordre": 5},
                {"nom": "sous_type_penal", "valeur": "Simple Police", "unite": None, "ordre": 10},
                {"nom": "sous_type_penal", "valeur": "Criminel", "unite": None, "ordre": 15},
                {"nom": "qualite_type", "valeur": "Personne physique", "unite": None, "ordre": 5},
                {"nom": "qualite_type", "valeur": "Personne morale", "unite": None, "ordre": 15},
                {"nom": "role_type", "valeur": "Demandeur", "unite": None, "ordre": 15},
                {"nom": "role_type", "valeur": "Defendeur", "unite": None, "ordre": 10},
                {"nom": "quota_echange_conclusion_civil", "valeur": "3", "unite": None, "ordre": 10},
                {"nom": "sous_type_jugement_defavorable", "valeur": "jugement_par_defaut", "unite": None, "ordre": 10},
                {"nom": "sous_type_jugement_defavorable", "valeur": "jugement_contradictoire", "unite": None, "ordre": 5}
            ]

            for p in params_to_create:
                exists = db.query(ParamGeneral).filter(
                    ParamGeneral.nom == p["nom"],
                    ParamGeneral.valeur == p["valeur"]
                ).first()
                if exists:
                    print(f"Paramètre '{p['nom']}' avec valeur '{p['valeur']}' déjà existant, skip")
                    continue

                param = ParamGeneral(
                    nom=p["nom"],
                    valeur=p["valeur"],
                    unite=p["unite"],
                    ordre=p["ordre"]
                )
                db.add(param)
                print(f"Création du paramètre '{p['nom']}' avec valeur '{p['valeur']}'")

            db.commit()
            db.close()
            break

        except OperationalError as e:
            print(f"Erreur de connexion à la DB (tentative {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"Attente de {delay} secondes avant nouvelle tentative...")
                time.sleep(delay)
            else:
                print("Échec de connexion à la base de données après plusieurs tentatives.")
                raise
