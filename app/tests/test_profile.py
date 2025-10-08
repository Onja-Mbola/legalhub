import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base_class import Base
from app.db.session import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_profile_page_requires_authentication(client):
    response = client.get("/profil")
    assert response.status_code == 401


def test_password_strength_validation():
    from app.utils.validators import validate_password_strength

    result = validate_password_strength("123")
    assert result["score"] == 1
    assert not result["is_valid"]

    result = validate_password_strength("SecurePass123!")
    assert result["score"] == 5
    assert result["is_valid"]


def test_email_format_validation():
    from app.utils.validators import validate_email_format

    assert validate_email_format("test@example.com") == True
    assert validate_email_format("invalid-email") == False
    assert validate_email_format("test@") == False