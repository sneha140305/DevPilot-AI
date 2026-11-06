import pytest
from app.db.database import initialize_database
from app.main import app
from app.repositories import project_repository
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_projects.db"

    initialize_database(db_path)

    monkeypatch.setattr(
        project_repository,
        "DATABASE_PATH",
        db_path,
    )

    project_repository.create_project(
        upload_id="a" * 32,
        original_filename="main.py",
        upload_type="python",
        db_path=db_path,
    )

    project_repository.create_project(
        upload_id="b" * 32,
        original_filename="project.zip",
        upload_type="zip",
        db_path=db_path,
    )

    return db_path


def test_get_all_projects(test_db):
    response = client.get("/api/v1/projects/")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total_projects"] == 2
    assert len(data["projects"]) == 2


def test_get_project_details(test_db):
    response = client.get(
        f"/api/v1/projects/{'a' * 32}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["project"]["original_filename"] == "main.py"


def test_project_not_found(test_db):
    response = client.get(
        f"/api/v1/projects/{'c' * 32}"
    )

    assert response.status_code == 404


def test_invalid_upload_id(test_db):
    response = client.get(
        "/api/v1/projects/invalid-id"
    )

    assert response.status_code == 400