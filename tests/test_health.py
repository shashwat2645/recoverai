from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "RecoverAI" in response.text


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
