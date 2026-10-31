import pytest
from app.core.config import settings
from app.main import app
from app.services import upload_service
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):

    monkeypatch.setattr(
        upload_service,
        "UPLOAD_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        settings,
        "MAX_UPLOAD_SIZE_MB",
        1,
    )

    return TestClient(app)


def test_successful_python_upload(client, tmp_path):

    content = b"def add(a, b):\n    return a + b\n"

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "calculator.py",
                content,
                "text/x-python",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True
    assert data["filename"] == "calculator.py"
    assert data["status"] == "uploaded"

    upload_id = data["upload_id"]

    stored_file = tmp_path / upload_id / "source.py"

    assert stored_file.exists()
    assert stored_file.read_bytes() == content


def test_reject_non_python_file(client):

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "document.txt",
                b"Hello World",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415

    assert (
        response.json()["detail"]["code"]
        == "UNSUPPORTED_FILE_TYPE"
    )


def test_reject_empty_file(client):

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "empty.py",
                b"",
                "text/x-python",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "EMPTY_FILE"
    )


def test_reject_large_file(client):

    large_content = b"a" * (1024 * 1024 + 1)

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "large.py",
                large_content,
                "text/x-python",
            )
        },
    )

    assert response.status_code == 413

    assert (
        response.json()["detail"]["code"]
        == "FILE_TOO_LARGE"
    )


def test_filename_path_traversal_is_sanitized(client, tmp_path):

    content = b"print('safe')"

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "../../outside.py",
                content,
                "text/x-python",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "outside.py"

    stored_file = (
        tmp_path
        / data["upload_id"]
        / "source.py"
    )

    assert stored_file.exists()

    assert not (tmp_path.parent / "outside.py").exists()


def test_each_upload_gets_unique_id(client):

    content = b"print('hello')"

    first_response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "first.py",
                content,
                "text/x-python",
            )
        },
    )

    second_response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "second.py",
                content,
                "text/x-python",
            )
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_id = first_response.json()["upload_id"]
    second_id = second_response.json()["upload_id"]

    assert first_id != second_id