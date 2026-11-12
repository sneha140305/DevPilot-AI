import pytest
from app.api.routes import test_execution
from app.main import app
from app.services.test_execution_service import TestExecutionError
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_execute_tests_success(client, monkeypatch):
    expected_response = {
    "success": True,
    "upload_id": "a" * 32,
    "status": "passed",
    "exit_code": 0,
    "stdout": "1 passed",
    "stderr": "",
    "test_file": "test_generated.py",
    "tests_total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": 0,
    "xfailed": 0,
    "xpassed": 0,
    "duration_seconds": None,
    "summary_available": False,
    "failure_details": [],
}

    monkeypatch.setattr(
        test_execution,
        "run_generated_tests",
        lambda upload_id: expected_response,
    )

    response = client.post(
        f"/api/v1/execute-tests/{'a' * 32}"
    )

    assert response.status_code == 200
    assert response.json() == expected_response


def test_execute_tests_invalid_upload_id(client):
    response = client.post(
        "/api/v1/execute-tests/invalid-id"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_execute_tests_without_generated_tests(
    client,
    monkeypatch,
):
    def fake_execution(upload_id):
        raise TestExecutionError(
            404,
            "TEST_GENERATION_NOT_FOUND",
            "Generate tests before requesting execution.",
        )

    monkeypatch.setattr(
        test_execution,
        "run_generated_tests",
        fake_execution,
    )

    response = client.post(
        f"/api/v1/execute-tests/{'b' * 32}"
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]["code"]
        == "TEST_GENERATION_NOT_FOUND"
    )


def test_execute_tests_docker_unavailable(
    client,
    monkeypatch,
):
    def fake_execution(upload_id):
        raise TestExecutionError(
            503,
            "DOCKER_UNAVAILABLE",
            "Docker CLI is not available.",
        )

    monkeypatch.setattr(
        test_execution,
        "run_generated_tests",
        fake_execution,
    )

    response = client.post(
        f"/api/v1/execute-tests/{'c' * 32}"
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DOCKER_UNAVAILABLE"


def test_execute_tests_timeout(client, monkeypatch):
    def fake_execution(upload_id):
        raise TestExecutionError(
            408,
            "TEST_EXECUTION_TIMEOUT",
            "Test execution exceeded the time limit.",
        )

    monkeypatch.setattr(
        test_execution,
        "run_generated_tests",
        fake_execution,
    )

    response = client.post(
        f"/api/v1/execute-tests/{'d' * 32}"
    )

    assert response.status_code == 408
    assert (
        response.json()["detail"]["code"]
        == "TEST_EXECUTION_TIMEOUT"
    )


def test_execute_tests_unexpected_error(
    client,
    monkeypatch,
):
    def fake_execution(upload_id):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr(
        test_execution,
        "run_generated_tests",
        fake_execution,
    )

    response = client.post(
        f"/api/v1/execute-tests/{'e' * 32}"
    )

    assert response.status_code == 500
    assert (
        response.json()["detail"]["code"]
        == "TEST_EXECUTION_ERROR"
    )