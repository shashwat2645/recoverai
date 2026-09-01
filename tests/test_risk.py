from fastapi.testclient import TestClient
from app.main import app
from app.services.risk_service import RiskService

client = TestClient(app)


def test_risk_score_calculation():
    # Transient high-priority failure
    high_score, category = RiskService.calculate_risk("BAD_REQUEST_PAYMENT_TIMED_OUT", 5000.0)
    assert high_score >= 0.90
    assert category == "TRANSIENT_TECHNICAL_FAILURE"

    # Liquidity failure
    med_score, med_cat = RiskService.calculate_risk("INSUFFICIENT_FUNDS", 2000.0)
    assert 0.60 <= med_score <= 0.80
    assert med_cat == "CUSTOMER_LIQUIDITY_OR_LIMIT"

    # Invalid card failure
    low_score, low_cat = RiskService.calculate_risk("EXPIRED_CARD", 1000.0)
    assert low_score <= 0.40
    assert low_cat == "CARD_OR_ACCOUNT_INVALID"


def test_automatic_case_creation_on_event_ingestion():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Risk Test Merchant",
        "email": "risk@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "risk@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate Payment Failure Event
    sim_payload = {
        "event_type": "payment.failed",
        "amount": 3500.00,
        "currency": "INR",
        "customer_email": "riskcustomer@example.com",
        "failure_reason": "BAD_REQUEST_PAYMENT_TIMED_OUT"
    }

    sim_res = client.post("/api/v1/events/simulate", json=sim_payload, headers=headers)
    assert sim_res.status_code == 201

    # 3. Verify that a RecoveryCase was automatically created and is queryable via GET /api/v1/cases
    cases_res = client.get("/api/v1/cases", headers=headers)
    assert cases_res.status_code == 200
    cases_data = cases_res.json()
    assert cases_data["total"] == 1

    case = cases_data["cases"][0]
    assert case["status"] == "DETECTED"
    assert case["amount_at_risk"] == 3500.00
    assert case["customer_email"] == "riskcustomer@example.com"
    assert case["risk_score"] >= 0.90

    # 4. Query single case by ID
    single_case_res = client.get(f"/api/v1/cases/{case['id']}", headers=headers)
    assert single_case_res.status_code == 200
    assert single_case_res.json()["id"] == case["id"]
