import pytest
from app.models.anomaly import Anomaly
from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset

def _auth_header(client, email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

def test_ml_health_endpoint(client):
    resp = client.get("/ml/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "AUTHORIZATION" in data["models"]
    assert "CLAIMS" in data["models"]
    assert "PHARMACY" in data["models"]

def test_ml_predict_authorization(client):
    payload = {
        "authorization_id": "AUTH-101",
        "charged_amount": 500.0,
        "requested_quantity": 5,
        "approval_status": "approved",
    }
    resp = client.post("/ml/predict?source_type=AUTHORIZATION", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "is_anomaly" in data
    assert "severity" in data
    assert "model" in data

def test_ml_predict_claims_rules(client):
    payload = {
        "claim_id": "CLM-NEGATIVE",
        "claim_amount": -150.0,
        "Issuer_Claims_Received_Out_of_Network": 10,
        "Issuer_Claims_Denied_Out_of_Network": 25,  # Denials > Received
    }
    resp = client.post("/ml/predict?source_type=CLAIMS", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_anomaly"] is True
    assert data["source_type"] == "CLAIMS"
    assert data["rule_engine"]["anomaly"] is True

def test_ml_predict_pharmacy_rules(client):
    payload = {
        "prescription_id": "RX-ANOM",
        "Tot_Clms": -5,
        "Tot_Drug_Cst": -200.0,
    }
    resp = client.post("/ml/predict?source_type=PHARMACY", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_anomaly"] is True
    assert data["source_type"] == "PHARMACY"
    assert data["rule_engine"]["anomaly"] is True

def test_sla_risk_endpoint(client, admin_user, sample_anomaly):
    headers = _auth_header(client, admin_user.email, "Admin1234!")
    resp = client.get(f"/anomalies/{sample_anomaly.id}/sla", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "target_hours" in data
    assert "sla_status" in data
    assert "breach_probability" in data
    assert "sla_risk_tier" in data

def test_steward_feedback_endpoint(client, admin_user, sample_anomaly):
    headers = _auth_header(client, admin_user.email, "Admin1234!")
    payload = {
        "action": "ACCEPTED",
        "rating": 5,
        "notes": "Verified against source system and corrected.",
    }
    resp = client.post(f"/anomalies/{sample_anomaly.id}/feedback", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "ACCEPTED"
    assert data["status"] == "RESOLVED"
