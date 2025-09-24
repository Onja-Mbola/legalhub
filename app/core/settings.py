import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    SMTP_USER: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_HOST: str = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False

    FROM_EMAIL: str = os.getenv("FROM_EMAIL")

    CABINET_ADRESSE: str = os.getenv("CABINET_ADRESSE", "Adresse du Cabinet")
    CABINET_TELEPHONE: str = os.getenv("CABINET_TELEPHONE", "Téléphone")

settings = Settings()
