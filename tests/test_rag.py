from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_policy_creation_and_rag_retrieval():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "RAG Merchant Ltd",
        "email": "rag@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "rag@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add Policy Document via POST /api/v1/policies
    policy_payload = {
        "title": "VIP High Value Recovery Rules",
        "policy_type": "RETRY",
        "content": "For transactions above 5000 INR, generate instant payment link and send SMS reminder within 15 minutes."
    }

    create_res = client.post("/api/v1/policies", json=policy_payload, headers=headers)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["title"] == "VIP High Value Recovery Rules"
    assert data["policy_type"] == "RETRY"

    # 3. List Policy Documents
    list_res = client.get("/api/v1/policies", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 4. Simulate Failure & Run AI Agent Analysis to test RAG Context Injection
    sim_res = client.post(
        "/api/v1/events/simulate",
        json={
            "event_type": "payment.failed",
            "amount": 7500.00,
            "customer_email": "vipcustomer@example.com",
            "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
        },
        headers=headers
    )
    assert sim_res.status_code == 201

    case_id = client.get("/api/v1/cases", headers=headers).json()["cases"][0]["id"]

    analyze_res = client.post(f"/api/v1/cases/{case_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()
    assert analyze_data["reasoning"]["recommended_action"] in ["GENERATE_PAYMENT_LINK", "SEND_REMINDER", "SCHEDULE_RETRY"]
