from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_merchant_registration_and_login():
    payload = {
        "name": "Auth Merchant Ltd",
        "email": "auth@merchant.com",
        "password": "SecurePassword123!",
        "razorpay_key_id": "rzp_test_99999",
        "razorpay_key_secret": "rzp_secret_99999"
    }

    # 1. Register Merchant
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "auth@merchant.com"
    assert data["name"] == "Auth Merchant Ltd"
    assert "id" in data

    # 2. Duplicate Registration Rejection
    dup_response = client.post("/api/v1/auth/register", json=payload)
    assert dup_response.status_code == 400
    assert "already exists" in dup_response.json()["detail"]

    # 3. Login with correct credentials
    login_payload = {
        "email": "auth@merchant.com",
        "password": "SecurePassword123!"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 4. Access Protected /me Endpoint with Bearer Token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "auth@merchant.com"

    # 5. Access Protected Endpoint with Invalid Token
    bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
    bad_response = client.get("/api/v1/auth/me", headers=bad_headers)
    assert bad_response.status_code == 401
