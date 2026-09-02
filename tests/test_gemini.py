from fastapi.testclient import TestClient
from app.main import app
from app.services.gemini_service import GeminiService

client = TestClient(app)


def test_gemini_service_structured_reasoning():
    result = GeminiService.analyze_payment_failure(
        failure_reason="BAD_REQUEST_PAYMENT_TIMED_OUT",
        amount=2500.00,
        customer_email="test@example.com",
        policy_context="Max retries: 3. Instant payment link generation allowed."
    )

    assert result.root_cause is not None
    assert result.recommended_action in ["GENERATE_PAYMENT_LINK", "SEND_REMINDER", "SCHEDULE_RETRY", "MARK_UNRECOVERABLE"]
    assert 0.0 <= result.confidence_score <= 1.0
    assert isinstance(result.stopping_rules_triggered, list)


def test_gemini_service_stopping_rules():
    result = GeminiService.analyze_payment_failure(
        failure_reason="BAD_REQUEST_PAYMENT_TIMED_OUT",
        amount=2500.00,
        customer_email="test@example.com",
        recovery_attempts=3  # Max attempts reached
    )

    assert result.recommended_action == "MARK_UNRECOVERABLE"
    assert "MAX_RETRIES_EXCEEDED" in result.stopping_rules_triggered


def test_ai_test_reasoning_endpoint():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "AI Test Merchant",
        "email": "ai@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "ai@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Invoke Test AI Reasoning Endpoint
    ai_req = {
        "failure_reason": "INSUFFICIENT_FUNDS",
        "amount": 1999.00,
        "customer_email": "customer@example.com",
        "policy_context": "Send reminder SMS before retrying."
    }

    res = client.post("/api/v1/ai/test-reasoning", json=ai_req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "root_cause" in data
    assert data["recommended_action"] in ["GENERATE_PAYMENT_LINK", "SEND_REMINDER", "SCHEDULE_RETRY", "MARK_UNRECOVERABLE"]
    assert "confidence_score" in data
