from fastapi.testclient import TestClient
from app.main import app
from app.services.razorpay_service import RazorpayService

client = TestClient(app)


def test_razorpay_service_link_generation():
    result = RazorpayService.create_payment_link(
        amount=1499.00,
        currency="INR",
        description="Test Recovery Link",
        customer_name="Alice Smith",
        customer_email="alice@example.com"
    )

    assert "id" in result
    assert "short_url" in result
    assert result["amount"] == 149900  # Amount in paise
    assert result["currency"] == "INR"


def test_razorpay_payment_link_endpoint():
    # 1. Register & Login Merchant
    reg_payload = {
        "name": "Razorpay Test Merchant",
        "email": "razorpay@merchant.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "razorpay@merchant.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Request Payment Link Creation
    req_payload = {
        "amount": 2999.00,
        "currency": "INR",
        "description": "Subscription Retry Link",
        "customer_name": "Bob Johnson",
        "customer_email": "bob@example.com"
    }

    response = client.post("/api/v1/razorpay/payment-link", json=req_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "payment_link_id" in data
    assert "short_url" in data
    assert data["amount"] == 2999.00
    assert data["status"] == "created"
