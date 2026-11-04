from app.main import app
from app.services.upload_service import UPLOAD_ROOT
from fastapi.testclient import TestClient

client = TestClient(app)


def create_python_upload():
    upload_response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "calculator.py",
                b"def add(a, b):\n    return a + b\n",
                "text/x-python",
            )
        },
    )

    assert upload_response.status_code == 201
    return upload_response.json()["upload_id"]


def test_generate_tests_for_uploaded_file():
    upload_id = create_python_upload()

    response = client.post(
        f"/api/v1/generate-tests/{upload_id}/calculator.py"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total_functions"] == 1
    assert data["total_tests"] == 1
    assert "test_add_exists" in data["test_code"]


def test_generate_tests_invalid_upload_id():
    response = client.post(
        "/api/v1/generate-tests/invalid-id/calculator.py"
    )

    assert response.status_code == 400


def test_generate_tests_missing_upload():
    response = client.post(
        f"/api/v1/generate-tests/{'a' * 32}/calculator.py"
    )

    assert response.status_code == 404


def test_generate_tests_invalid_filename():
    upload_id = create_python_upload()

    response = client.post(
        f"/api/v1/generate-tests/{upload_id}/calculator.txt"
    )

    assert response.status_code == 400


def test_original_uploaded_file_is_unchanged():
    upload_id = create_python_upload()

    source_file = UPLOAD_ROOT / upload_id / "source.py"
    original_content = source_file.read_bytes()

    client.post(
        f"/api/v1/generate-tests/{upload_id}/calculator.py"
    )

    assert source_file.read_bytes() == original_content