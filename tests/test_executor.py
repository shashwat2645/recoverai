from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_action_execution_and_guardrails():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Executor Merchant",
        "email": "executor@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "executor@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate Payment Failure Event
    sim_res = client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 3499.00,
            "customer_email": "exec_customer@example.com",
            "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
        },
        headers=headers
    )
    assert sim_res.status_code == 201

    case_id = client.get("/api/v1/cases", headers=headers).json()["cases"][0]["id"]

    # 3. Analyze Case with AI Agent
    client.post(f"/api/v1/cases/{case_id}/analyze", headers=headers)

    # 4. Execute Recommended Bounded Action (GENERATE_PAYMENT_LINK)
    exec_res = client.post(f"/api/v1/cases/{case_id}/execute", headers=headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["execution_status"] == "SUCCESS"
    assert exec_data["status"] == "RECOVERING"
    assert "short_url" in exec_data["details"]

    # 5. Attempt Forbidden Action (REFUND) - Guardrail Failure Expected
    bad_exec_res = client.post(
        f"/api/v1/cases/{case_id}/execute",
        json={"action_override": "REFUND"},
        headers=headers
    )
    assert bad_exec_res.status_code == 403
    assert "Guardrail Blocked" in bad_exec_res.json()["detail"]
