import pytest
from app.api.routes import test_execution
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def upload_id():
    return "a" * 32


@pytest.fixture
def sample_execution(upload_id):
    return {
        "id": 1,
        "upload_id": upload_id,
        "result": {
            "success": True,
            "status": "passed",
            "exit_code": 0,
            "tests_total": 2,
            "passed": 2,
            "failed": 0,
        },
        "created_at": "2026-11-12 12:00:00",
    }


def test_get_execution_history_success(
    client,
    monkeypatch,
    upload_id,
    sample_execution,
):
    monkeypatch.setattr(
        test_execution,
        "list_test_executions",
        lambda uid: [sample_execution],
    )

    response = client.get(
        f"/api/v1/execute-tests/{upload_id}/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["upload_id"] == upload_id
    assert data["total_executions"] == 1
    assert data["executions"][0]["result"]["status"] == "passed"


def test_get_execution_history_empty(
    client,
    monkeypatch,
    upload_id,
):
    monkeypatch.setattr(
        test_execution,
        "list_test_executions",
        lambda uid: [],
    )

    response = client.get(
        f"/api/v1/execute-tests/{upload_id}/history"
    )

    assert response.status_code == 200
    assert response.json()["total_executions"] == 0
    assert response.json()["executions"] == []


def test_get_execution_history_invalid_upload_id(client):
    response = client.get(
        "/api/v1/execute-tests/invalid-id/history"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_get_latest_execution_success(
    client,
    monkeypatch,
    upload_id,
    sample_execution,
):
    monkeypatch.setattr(
        test_execution,
        "get_latest_test_execution",
        lambda uid: sample_execution,
    )

    response = client.get(
        f"/api/v1/execute-tests/{upload_id}/latest"
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["result"]["status"] == "passed"


def test_get_latest_execution_not_found(
    client,
    monkeypatch,
    upload_id,
):
    monkeypatch.setattr(
        test_execution,
        "get_latest_test_execution",
        lambda uid: None,
    )

    response = client.get(
        f"/api/v1/execute-tests/{upload_id}/latest"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "TEST_EXECUTION_NOT_FOUND"
    )


def test_get_latest_execution_invalid_upload_id(client):
    response = client.get(
        "/api/v1/execute-tests/invalid-id/latest"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"