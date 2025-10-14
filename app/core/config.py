from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    ENV: str = "development"
    PORT: int = 8000

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "mdgmanjamanja@gmail.com"

    CABINET_NOM: str = ""
    NOM_AVOCAT: str = ""
    CABINET_ADRESSE: str = ""
    CABINET_TELEPHONE: str = ""
    MAIL_CABINET: str = ""
    IBAN: str = ""
    BIC: str = ""
    NUMERO_MOBILE: str = ""
    NOM_MOBILE: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = False
    PASSWORD_CHANGE_MAX_ATTEMPTS: int = 5
    PASSWORD_CHANGE_WINDOW_MINUTES: int = 15

    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "legalhub-dossiers"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
