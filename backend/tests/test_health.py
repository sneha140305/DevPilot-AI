from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["message"] == "Welcome to DevPilot AI API"


def test_health_endpoint():

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["status"] == "healthy"

    assert data["service"] == "DevPilot AI"


def test_invalid_endpoint():

    response = client.get("/invalid-endpoint")

    assert response.status_code == 404