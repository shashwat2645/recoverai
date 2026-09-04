from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_metrics_aggregation():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Dashboard Merchant",
        "email": "dashboard@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "dashboard@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate Failures
    client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 2500.00,
            "customer_email": "c1@example.com",
            "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
        },
        headers=headers
    )
    client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 1500.00,
            "customer_email": "c2@example.com",
            "failure_reason": "INSUFFICIENT_FUNDS"
        },
        headers=headers
    )

    # 3. Fetch cases and run analyze + execute on first case
    cases_data = client.get("/api/v1/cases", headers=headers).json()["cases"]
    c1_id = cases_data[0]["id"]
    client.post(f"/api/v1/cases/{c1_id}/analyze", headers=headers)
    client.post(f"/api/v1/cases/{c1_id}/execute", headers=headers)

    # 4. Trigger guardrail block (attempt REFUND) to verify false actions avoided count
    client.post(f"/api/v1/cases/{c1_id}/execute", json={"action_override": "REFUND"}, headers=headers)

    # 5. Query Dashboard Metrics
    metrics_res = client.get("/api/v1/dashboard/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()

    assert metrics["total_failed_payments"] == 2
    assert metrics["revenue_at_risk"] == 4000.00
    assert metrics["recovery_attempts"] >= 1
    assert metrics["false_actions_avoided"] == 1
    assert "status_breakdown" in metrics
