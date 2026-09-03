from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_agent_case_analysis():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Agent Test Merchant",
        "email": "agent@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "agent@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate Payment Failure Event (creates DETECTED case)
    sim_res = client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 4999.00,
            "customer_email": "agentcustomer@example.com",
            "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
        },
        headers=headers
    )
    assert sim_res.status_code == 201

    # 3. Get Case ID
    cases_res = client.get("/api/v1/cases", headers=headers)
    case_id = cases_res.json()["cases"][0]["id"]

    # 4. Trigger AI Agent Analysis via API
    analyze_res = client.post(f"/api/v1/cases/{case_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["case_id"] == case_id
    assert data["status"] == "ACTION_REQUIRED"
    assert data["reasoning"]["recommended_action"] in ["GENERATE_PAYMENT_LINK", "SEND_REMINDER", "SCHEDULE_RETRY"]
    assert data["reasoning"]["confidence_score"] > 0.50
