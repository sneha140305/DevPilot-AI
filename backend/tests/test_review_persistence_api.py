import pytest
from app.db.database import initialize_database
from app.main import app
from app.repositories import review_repository
from app.repositories.project_repository import create_project
from app.services import upload_service
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        upload_service,
        "UPLOAD_ROOT",
        tmp_path,
    )

    test_db = tmp_path / "test_devpilot.db"

    monkeypatch.setattr(
        review_repository,
        "DATABASE_PATH",
        test_db,
    )

    initialize_database(test_db)

    return TestClient(app)


def create_project_files(tmp_path, upload_id):
    project_directory = (
        tmp_path / upload_id / "project"
    )

    project_directory.mkdir(parents=True)

    source_file = project_directory / "main.py"

    source_file.write_text(
        "import os\n\n"
        "def calculate():\n"
        "    return 10\n",
        encoding="utf-8",
    )

    create_project(
        upload_id=upload_id,
        original_filename="test_project.zip",
        upload_type="zip",
        db_path=review_repository.DATABASE_PATH,
    )


def test_review_api_persists_result(client, tmp_path):
    upload_id = "a" * 32

    create_project_files(tmp_path, upload_id)

    response = client.post(
        f"/api/v1/review/{upload_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["upload_id"] == upload_id
    assert "reviews" in data

    history_response = client.get(
        f"/api/v1/review/{upload_id}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["success"] is True
    assert len(history["reviews"]) == 1


def test_get_latest_review(client, tmp_path):
    upload_id = "b" * 32

    create_project_files(tmp_path, upload_id)

    client.post(
        f"/api/v1/review/{upload_id}"
    )

    response = client.get(
        f"/api/v1/review/{upload_id}/latest"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["upload_id"] == upload_id
    assert "result" in data


def test_review_history_empty(client, tmp_path):
    upload_id = "c" * 32

    create_project_files(tmp_path, upload_id)

    response = client.get(
        f"/api/v1/review/{upload_id}/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["reviews"] == []


def test_latest_review_not_found(client, tmp_path):
    upload_id = "d" * 32

    create_project_files(tmp_path, upload_id)

    response = client.get(
        f"/api/v1/review/{upload_id}/latest"
    )

    assert response.status_code == 404
    