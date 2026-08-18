import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import hash_password
from app.utils.enums import UserRole

# In-memory SQLite for tests (schema is DB-agnostic for auth)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    return TestingSessionLocal()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    user = User(
        id=str(uuid.uuid4()),
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("Admin1234!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def worker_user(db):
    user = User(
        id=str(uuid.uuid4()),
        name="Worker User",
        email="worker@example.com",
        password_hash=hash_password("Worker1234!"),
        role=UserRole.WORKER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
