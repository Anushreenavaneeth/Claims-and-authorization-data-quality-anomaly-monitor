"""
Anomaly API tests — Day 3
Run: pytest tests/test_anomalies.py -v
"""
import uuid
from app.models.anomaly import Anomaly
from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset


# ── Helpers ───────────────────────────────────────────────────────────────

def _auth_header(client, email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


VALID_PAYLOAD = {
    "source_dataset":  "CLAIMS",
    "record_id":       "C999",
    "anomaly_type":    "NEGATIVE_VALUE",
    "severity":        "HIGH",
    "affected_field":  "claim_amount",
    "error_message":   "claim_amount is -50.00",
    "likely_cause":    "Data entry error",
    "recommended_fix": "Validate against source",
    "raw_record":      {"claim_id": "C999", "amount": -50.0},
}


# ── List anomalies ─────────────────────────────────────────────────────────

def test_list_anomalies_empty(client, admin_user):
    resp = client.get("/anomalies", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_anomalies_returns_records(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


def test_list_anomalies_filter_severity(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?severity=HIGH", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(a["severity"] == "HIGH" for a in items)


def test_list_anomalies_filter_status(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?status=OPEN", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(a["status"] == "OPEN" for a in items)


def test_list_anomalies_search(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?search=C003", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["record_id"] == "C003"


def test_list_anomalies_pagination(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?page=1&page_size=2", headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


def test_list_anomalies_requires_auth(client):
    resp = client.get("/anomalies")
    assert resp.status_code in (401, 403)


def test_worker_can_list_anomalies(client, worker_user, multiple_anomalies):
    resp = client.get("/anomalies", headers=_auth_header(client, "worker@example.com", "Worker1234!"))
    assert resp.status_code == 200


# ── Get single anomaly ────────────────────────────────────────────────────

def test_get_anomaly_by_id(client, admin_user, sample_anomaly):
    resp = client.get(f"/anomalies/{sample_anomaly.id}",
                      headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sample_anomaly.id
    assert data["record_id"] == "C001"
    assert data["severity"] == "HIGH"
    assert data["raw_record"]["claim_amount"] == -50.0


def test_get_anomaly_not_found(client, admin_user):
    resp = client.get(f"/anomalies/{uuid.uuid4()}",
                      headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 404


# ── Create anomaly ────────────────────────────────────────────────────────

def test_admin_can_create_anomaly(client, admin_user):
    resp = client.post("/anomalies", json=VALID_PAYLOAD,
                       headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["record_id"] == "C999"
    assert data["status"] == "OPEN"
    assert "id" in data


def test_worker_cannot_create_anomaly(client, worker_user):
    resp = client.post("/anomalies", json=VALID_PAYLOAD,
                       headers=_auth_header(client, "worker@example.com", "Worker1234!"))
    assert resp.status_code == 403


def test_create_anomaly_missing_field(client, admin_user):
    bad = {**VALID_PAYLOAD}
    del bad["error_message"]
    resp = client.post("/anomalies", json=bad,
                       headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 422


# ── Update status ─────────────────────────────────────────────────────────

def test_update_anomaly_status(client, admin_user, sample_anomaly):
    resp = client.patch(
        f"/anomalies/{sample_anomaly.id}/status",
        json={"status": "IN_PROGRESS"},
        headers=_auth_header(client, "admin@example.com", "Admin1234!"),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


def test_update_status_to_resolved(client, admin_user, sample_anomaly):
    resp = client.patch(
        f"/anomalies/{sample_anomaly.id}/status",
        json={"status": "RESOLVED"},
        headers=_auth_header(client, "admin@example.com", "Admin1234!"),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


def test_update_status_invalid_value(client, admin_user, sample_anomaly):
    resp = client.patch(
        f"/anomalies/{sample_anomaly.id}/status",
        json={"status": "NONSENSE"},
        headers=_auth_header(client, "admin@example.com", "Admin1234!"),
    )
    assert resp.status_code == 422


def test_update_status_not_found(client, admin_user):
    resp = client.patch(
        f"/anomalies/{uuid.uuid4()}/status",
        json={"status": "RESOLVED"},
        headers=_auth_header(client, "admin@example.com", "Admin1234!"),
    )
    assert resp.status_code == 404


def test_worker_can_update_status(client, worker_user, sample_anomaly):
    resp = client.patch(
        f"/anomalies/{sample_anomaly.id}/status",
        json={"status": "IN_PROGRESS"},
        headers=_auth_header(client, "worker@example.com", "Worker1234!"),
    )
    assert resp.status_code == 200


# ── Rerun ─────────────────────────────────────────────────────────────────

def test_admin_can_trigger_rerun(client, admin_user, sample_anomaly):
    resp = client.post(f"/anomalies/{sample_anomaly.id}/rerun",
                       headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    assert "Re-run triggered" in resp.json()["message"]


def test_worker_cannot_trigger_rerun(client, worker_user, sample_anomaly):
    resp = client.post(f"/anomalies/{sample_anomaly.id}/rerun",
                       headers=_auth_header(client, "worker@example.com", "Worker1234!"))
    assert resp.status_code == 403


def test_rerun_not_found(client, admin_user):
    resp = client.post(f"/anomalies/{uuid.uuid4()}/rerun",
                       headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 404


# ── Source filter ─────────────────────────────────────────────────────────

def test_filter_by_source_claims(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?source=CLAIMS",
                      headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(a["source_dataset"] == "CLAIMS" for a in items)


def test_filter_by_source_pharmacy_empty(client, admin_user, multiple_anomalies):
    resp = client.get("/anomalies?source=PHARMACY",
                      headers=_auth_header(client, "admin@example.com", "Admin1234!"))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
