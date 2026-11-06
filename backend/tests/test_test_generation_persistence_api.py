from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def create_python_upload():
    """Create a Python upload using the existing upload API."""

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "calculator.py",
                b"def add(a, b):\n    return a + b\n",
                "text/x-python",
            )
        },
    )

    assert response.status_code == 201

    return response.json()["upload_id"]


def test_generate_tests_persists_result():
    upload_id = create_python_upload()

    response = client.post(
        f"/api/v1/generate-tests/{upload_id}/calculator.py"
    )

    assert response.status_code == 200

    generated = response.json()

    latest_response = client.get(
        f"/api/v1/generate-tests/{upload_id}/latest"
    )

    assert latest_response.status_code == 200

    latest = latest_response.json()

    assert latest["success"] is True
    assert latest["upload_id"] == upload_id
    assert latest["result"] == generated


def test_get_latest_test_generation():
    upload_id = create_python_upload()

    client.post(
        f"/api/v1/generate-tests/{upload_id}/calculator.py"
    )

    response = client.get(
        f"/api/v1/generate-tests/{upload_id}/latest"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["result"]["total_functions"] == 1
    assert data["result"]["total_tests"] == 1


def test_get_test_generation_history():
    upload_id = create_python_upload()

    for _ in range(2):
        response = client.post(
            f"/api/v1/generate-tests/{upload_id}/calculator.py"
        )

        assert response.status_code == 200

    history_response = client.get(
        f"/api/v1/generate-tests/{upload_id}/history"
    )

    assert history_response.status_code == 200

    data = history_response.json()

    assert data["success"] is True
    assert data["total_generations"] == 2
    assert len(data["history"]) == 2


def test_empty_test_generation_history():
    upload_id = create_python_upload()

    response = client.get(
        f"/api/v1/generate-tests/{upload_id}/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_generations"] == 0
    assert data["history"] == []


def test_latest_test_generation_not_found():
    upload_id = create_python_upload()

    response = client.get(
        f"/api/v1/generate-tests/{upload_id}/latest"
    )

    assert response.status_code == 404


def test_invalid_upload_id_for_history():
    response = client.get(
        "/api/v1/generate-tests/invalid-id/history"
    )

    assert response.status_code == 400