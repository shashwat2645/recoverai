from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_audit_log_tracking_and_query():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Audit Test Merchant",
        "email": "audit@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "audit@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate Payment Failure
    sim_res = client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 2999.00,
            "customer_email": "audit_customer@example.com",
            "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
        },
        headers=headers
    )
    assert sim_res.status_code == 201

    case_id = client.get("/api/v1/cases", headers=headers).json()["cases"][0]["id"]

    # 3. Analyze Case (generates AI_DIAGNOSIS audit log)
    analyze_res = client.post(f"/api/v1/cases/{case_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200

    # 4. Execute Action (generates ACTION_EXECUTION audit log)
    exec_res = client.post(f"/api/v1/cases/{case_id}/execute", headers=headers)
    assert exec_res.status_code == 200

    # 5. Query Audit Logs for Case
    case_audit_res = client.get(f"/api/v1/cases/{case_id}/audit-logs", headers=headers)
    assert case_audit_res.status_code == 200
    case_logs = case_audit_res.json()["audit_logs"]
    assert len(case_logs) >= 2

    event_types = [l["event_type"] for l in case_logs]
    assert "AI_DIAGNOSIS" in event_types
    assert "ACTION_EXECUTION" in event_types

    # 6. Query Global Merchant Audit Logs
    global_audit_res = client.get("/api/v1/audit-logs", headers=headers)
    assert global_audit_res.status_code == 200
    assert global_audit_res.json()["total"] >= 2
