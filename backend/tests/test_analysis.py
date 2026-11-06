import pytest
from app.db.database import initialize_database
from app.main import app
from app.repositories import analysis_repository
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
        analysis_repository,
        "DATABASE_PATH",
        test_db,
    )

    initialize_database(test_db)

    return TestClient(app)


def create_uploaded_project(
    tmp_path,
    upload_id,
    files,
):

    project_directory = (
        tmp_path / upload_id / "project"
    )

    project_directory.mkdir(
        parents=True,
    )

    for filename, content in files.items():

        file_path = project_directory / filename

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

    # Register the project in SQLite.
    create_project(
        upload_id=upload_id,
        original_filename="test_project.zip",
        upload_type="zip",
        db_path=analysis_repository.DATABASE_PATH,
    )


def test_analyze_clean_python_file(client, tmp_path):

    upload_id = "a" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": (
                "def add(a, b):\n"
                "    return a + b\n"
            )
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total_files"] == 1
    assert data["total_issues"] == 0


def test_detect_eval_usage(client, tmp_path):

    upload_id = "b" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": "result = eval('2 + 2')\n"
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "PY002"
        for issue in issues
    )


def test_detect_exec_usage(client, tmp_path):

    upload_id = "c" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": "exec('print(1)')\n"
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "PY003"
        for issue in issues
    )


def test_detect_bare_except(client, tmp_path):

    upload_id = "d" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": (
                "try:\n"
                "    print('hello')\n"
                "except:\n"
                "    pass\n"
            )
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "PY004"
        for issue in issues
    )


def test_detect_wildcard_import(client, tmp_path):

    upload_id = "e" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": "from math import *\n"
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "PY005"
        for issue in issues
    )


def test_detect_syntax_error(client, tmp_path):

    upload_id = "f" * 32

    create_uploaded_project(
        tmp_path,
        upload_id,
        {
            "main.py": "def broken(\n"
        },
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_issues"] == 1

    assert data["issues"][0]["rule_id"] == "PY001"

    assert data["files"][0]["status"] == "syntax_error"


def test_reject_invalid_upload_id(client):

    response = client.post(
        "/api/v1/analyze/../../invalid"
    )

    assert response.status_code in {400, 404, 405}


def test_reject_missing_upload(client):

    upload_id = "9" * 32

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 404