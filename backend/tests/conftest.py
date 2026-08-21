import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.anomaly import Anomaly  # noqa: ensure table created
from app.services.auth_service import hash_password
from app.utils.enums import UserRole, AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset

from sqlalchemy.pool import StaticPool

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
        phone_number=None,
        invite_token=None,
        invite_token_expires_at=None,
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
        phone_number=None,
        invite_token=None,
        invite_token_expires_at=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Anomaly fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def sample_anomaly(db):
    anomaly = Anomaly(
        id=str(uuid.uuid4()),
        source_dataset=SourceDataset.CLAIMS,
        record_id="C001",
        anomaly_type=AnomalyType.NEGATIVE_VALUE,
        severity=AnomalySeverity.HIGH,
        status=AnomalyStatus.OPEN,
        affected_field="claim_amount",
        error_message="claim_amount is -50.00, expected positive value",
        likely_cause="Data entry error in source system",
        recommended_fix="Validate against source claims system and correct the value",
        raw_record={"claim_id": "C001", "claim_amount": -50.00, "provider_id": "P123"},
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


@pytest.fixture
def multiple_anomalies(db):
    anomalies = [
        Anomaly(
            id=str(uuid.uuid4()),
            source_dataset=SourceDataset.CLAIMS,
            record_id=f"C00{i}",
            anomaly_type=AnomalyType.NEGATIVE_VALUE,
            severity=AnomalySeverity.HIGH if i % 2 == 0 else AnomalySeverity.MEDIUM,
            status=AnomalyStatus.OPEN,
            affected_field="claim_amount",
            error_message=f"Anomaly in record C00{i}",
            raw_record={"claim_id": f"C00{i}"},
        )
        for i in range(1, 6)
    ]
    for a in anomalies:
        db.add(a)
    db.commit()
    return anomalies


# ── Auth helper ────────────────────────────────────────────────────────────

def auth_header(client, email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
