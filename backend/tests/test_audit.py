import pytest
from app.models.audit_log import AuditLog

def _auth_header(client, email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

def test_get_audit_trail_empty(client, admin_user):
    headers = _auth_header(client, admin_user.email, "Admin1234!")
    resp = client.get("/audit-trail", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    # Admin login creates an audit log entry
    assert data["total"] >= 1

def test_create_and_query_audit_trail(client, admin_user):
    headers = _auth_header(client, admin_user.email, "Admin1234!")
    payload = {
        "anomaly_id": "anom-123",
        "record_id": "CLM-9999",
        "source_dataset": "CLAIMS",
        "action": "FIELD_CORRECTION",
        "field_name": "billed_amount",
        "old_value": "-100.00",
        "new_value": "100.00",
        "performed_by": "Dr. Steward",
        "notes": "Corrected sign error in billing sheet",
    }
    resp = client.post("/audit-trail", json=payload, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    assert created["record_id"] == "CLM-9999"
    assert created["action"] == "FIELD_CORRECTION"

    # Search query
    query_resp = client.get("/audit-trail?search=CLM-9999", headers=headers)
    assert query_resp.status_code == 200
    res_data = query_resp.json()
    assert res_data["total"] >= 1
    assert any(item["record_id"] == "CLM-9999" for item in res_data["items"])

def test_audit_log_on_anomaly_status_update(client, admin_user, sample_anomaly):
    headers = _auth_header(client, admin_user.email, "Admin1234!")
    
    patch_resp = client.patch(
        f"/anomalies/{sample_anomaly.id}/status",
        json={"status": "RESOLVED"},
        headers=headers,
    )
    assert patch_resp.status_code == 200

    audit_resp = client.get(f"/audit-trail?anomaly_id={sample_anomaly.id}", headers=headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total"] >= 1
    assert any("STATUS_UPDATE_RESOLVED" in item["action"] for item in audit_data["items"])
