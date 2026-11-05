from pathlib import Path

import pytest
from app.db.database import initialize_database
from app.repositories.project_repository import (
    create_project,
    get_project,
    list_projects,
)


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """
    Create a temporary database for repository tests.
    """

    db_path = tmp_path / "test_devpilot.db"

    initialize_database(db_path)

    return db_path


def test_create_project(test_db: Path):
    project = create_project(
        upload_id="abc123",
        original_filename="main.py",
        upload_type="python",
        db_path=test_db,
    )

    assert project is not None
    assert project["upload_id"] == "abc123"
    assert project["original_filename"] == "main.py"
    assert project["upload_type"] == "python"


def test_get_existing_project(test_db: Path):
    create_project(
        upload_id="abc123",
        original_filename="main.py",
        upload_type="python",
        db_path=test_db,
    )

    project = get_project(
        "abc123",
        db_path=test_db,
    )

    assert project is not None
    assert project["original_filename"] == "main.py"


def test_get_nonexistent_project(test_db: Path):
    project = get_project(
        "missing123",
        db_path=test_db,
    )

    assert project is None


def test_list_projects(test_db: Path):
    create_project(
        upload_id="project1",
        original_filename="main.py",
        upload_type="python",
        db_path=test_db,
    )

    create_project(
        upload_id="project2",
        original_filename="project.zip",
        upload_type="zip",
        db_path=test_db,
    )

    projects = list_projects(db_path=test_db)

    assert len(projects) == 2

    upload_ids = {
        project["upload_id"]
        for project in projects
    }

    assert upload_ids == {"project1", "project2"}


def test_project_contains_creation_timestamp(test_db: Path):
    project = create_project(
        upload_id="abc123",
        original_filename="main.py",
        upload_type="python",
        db_path=test_db,
    )

    assert project["created_at"] is not None