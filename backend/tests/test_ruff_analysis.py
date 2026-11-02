import pytest
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

    return TestClient(app)


def create_project(tmp_path, upload_id, source_code):

    project_directory = (
        tmp_path / upload_id / "project"
    )

    project_directory.mkdir(
        parents=True,
    )

    source_file = project_directory / "main.py"

    source_file.write_text(
        source_code,
        encoding="utf-8",
    )


def test_detect_unused_import(client, tmp_path):

    upload_id = "a" * 32

    create_project(
        tmp_path,
        upload_id,
        """
import os

def calculate():
    return 10
""",
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "RUFF-F401"
        for issue in issues
    )


def test_detect_undefined_name(client, tmp_path):

    upload_id = "b" * 32

    create_project(
        tmp_path,
        upload_id,
        """
def calculate():
    return undefined_variable
""",
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "RUFF-F821"
        for issue in issues
    )


def test_detect_unused_variable(client, tmp_path):

    upload_id = "c" * 32

    create_project(
        tmp_path,
        upload_id,
        """
def calculate():
    unused_value = 100
    return 10
""",
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "RUFF-F841"
        for issue in issues
    )


def test_detect_long_line(client, tmp_path):

    upload_id = "d" * 32

    create_project(
        tmp_path,
        upload_id,
        "result = " + ("1 + " * 30) + "1\n",
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    issues = response.json()["issues"]

    assert any(
        issue["rule_id"] == "RUFF-E501"
        for issue in issues
    )


def test_analysis_contains_severity_counts(client, tmp_path):

    upload_id = "e" * 32

    create_project(
        tmp_path,
        upload_id,
        "import os\n\nresult = undefined_variable\n",
    )

    response = client.post(
        f"/api/v1/analyze/{upload_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert "severity_counts" in data

    assert data["severity_counts"]["high"] >= 1
    assert data["severity_counts"]["medium"] >= 1