import io
import zipfile

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
        10,
    )

    monkeypatch.setattr(
        settings,
        "MAX_EXTRACTED_SIZE_MB",
        50,
    )

    monkeypatch.setattr(
        settings,
        "MAX_FILE_SIZE_MB",
        5,
    )

    monkeypatch.setattr(
        settings,
        "MAX_FILES_PER_PROJECT",
        100,
    )

    return TestClient(app)


def create_zip(files):

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:

        for filename, content in files.items():
            archive.writestr(filename, content)

    return buffer.getvalue()


def test_successful_zip_upload(client, tmp_path):

    zip_content = create_zip({
        "main.py": "print('hello')",
        "app/service.py": "def run(): pass",
        "README.md": "# Demo",
    })

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "project.zip",
                zip_content,
                "application/zip",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True

    assert sorted(data["python_files"]) == [
        "app/service.py",
        "main.py",
    ]

    project_directory = (
        tmp_path
        / data["upload_id"]
        / "project"
    )

    assert (project_directory / "main.py").exists()
    assert (project_directory / "app/service.py").exists()


def test_reject_invalid_zip(client):

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "invalid.zip",
                b"not a zip file",
                "application/zip",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "INVALID_ARCHIVE"
    )


def test_reject_zip_path_traversal(client, tmp_path):

    zip_content = create_zip({
        "../outside.py": "print('unsafe')",
        "main.py": "print('safe')",
    })

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "unsafe.zip",
                zip_content,
                "application/zip",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "ZIP_PATH_TRAVERSAL"
    )

    assert not (client.app.state.upload_root if hasattr(client.app.state, "upload_root") else tmp_path / "outside.py").exists()


def test_ignore_unnecessary_directories(client):

    zip_content = create_zip({
        "main.py": "print('hello')",
        ".git/config": "git data",
        "__pycache__/module.pyc": "cache data",
        ".venv/lib/test.py": "virtual environment",
    })

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "project.zip",
                zip_content,
                "application/zip",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["python_files"] == ["main.py"]


def test_reject_nested_zip(client):

    zip_content = create_zip({
        "main.py": "print('hello')",
        "nested.zip": "fake archive",
    })

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "nested.zip",
                zip_content,
                "application/zip",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "NESTED_ARCHIVE_NOT_ALLOWED"
    )


def test_reject_zip_without_python_files(client):

    zip_content = create_zip({
        "README.md": "# Project",
        "requirements.txt": "fastapi",
    })

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "documentation.zip",
                zip_content,
                "application/zip",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "NO_PYTHON_FILES"
    )