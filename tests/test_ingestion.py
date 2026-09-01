import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.webhook_security import verify_razorpay_signature

client = TestClient(app)


def test_hmac_signature_verification():
    secret = "test_webhook_secret_key"
    payload = b'{"event":"payment.failed","amount":1000}'
    signature = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_signature(payload, signature, secret) is True
    assert verify_razorpay_signature(payload, "invalid_sig", secret) is False


def test_webhook_ingestion_and_idempotency():
    # 1. Register a merchant first to accept webhooks
    reg_payload = {
        "name": "Webhook Merchant",
        "email": "webhook@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Prepare sample Razorpay webhook payload
    razorpay_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_event_9999",
                    "amount": 250000,  # 2500.00 INR in paise
                    "currency": "INR",
                    "email": "testcustomer@example.com",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT"
                }
            }
        }
    }

    # 3. Post webhook event (first time)
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=json.dumps(razorpay_payload),
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event_id"] == "pay_test_event_9999"
    assert data["is_duplicate"] is False

    # 4. Post IDENTICAL webhook event (second time - idempotency check)
    dup_response = client.post(
        "/api/v1/webhooks/razorpay",
        content=json.dumps(razorpay_payload),
        headers={"Content-Type": "application/json"}
    )
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["event_id"] == "pay_test_event_9999"
    assert dup_data["is_duplicate"] is True


def test_simulate_event_endpoint():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Sim Merchant",
        "email": "sim@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "sim@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Simulate payment failure event
    sim_payload = {
        "event_type": "payment.failed",
        "amount": 1999.00,
        "currency": "INR",
        "customer_email": "simcustomer@example.com",
        "failure_reason": "GATEWAY_ERROR"
    }

    sim_res = client.post("/api/v1/events/simulate", json=sim_payload, headers=headers)
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    assert sim_data["amount"] == 1999.00
    assert sim_data["customer_email"] == "simcustomer@example.com"
    assert sim_data["failure_reason"] == "GATEWAY_ERROR"
