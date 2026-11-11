from app.api.routes import fixes
from app.main import app
from app.services.ast_analyzer import AnalysisError
from fastapi.testclient import TestClient

client = TestClient(app)

UPLOAD_ID = "a" * 32
FIX_ID = "b" * 32

VALID_REQUEST = {
    "file_path": "source.py",
    "rule_id": "PY004",
    "line": 3,
}


def test_accept_fix_success(monkeypatch):
    expected = {
        "success": True,
        "fix_id": FIX_ID,
        "upload_id": UPLOAD_ID,
        "file_path": "source.py",
        "rule_id": "PY004",
        "line": 3,
        "accepted_path": "data/accepted_fixes/test/accepted.py",
        "original_sha256": "a" * 64,
        "accepted_sha256": "b" * 64,
        "validation_passed": True,
        "message": "Proposed fix accepted and saved successfully.",
        "created_at": "2026-11-11 12:00:00",
    }

    monkeypatch.setattr(
        fixes,
        "accept_proposed_fix",
        lambda **kwargs: expected,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}/accept",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_accept_fix_invalid_upload_id():
    response = client.post(
        "/api/v1/fix/invalid-id/accept",
        json=VALID_REQUEST,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_accept_fix_invalid_request():
    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}/accept",
        json={
            "file_path": "source.py",
            "rule_id": "PY004",
            "line": 0,
        },
    )

    assert response.status_code == 422


def test_accept_fix_analysis_error(monkeypatch):
    def raise_error(**kwargs):
        raise AnalysisError(
            404,
            "SOURCE_FILE_NOT_FOUND",
            "The requested Python file was not found.",
        )

    monkeypatch.setattr(
        fixes,
        "accept_proposed_fix",
        raise_error,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}/accept",
        json=VALID_REQUEST,
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "SOURCE_FILE_NOT_FOUND"


def test_accept_fix_unsupported_rule(monkeypatch):
    def raise_error(**kwargs):
        raise ValueError("Automatic fixes are not supported.")

    monkeypatch.setattr(
        fixes,
        "accept_proposed_fix",
        raise_error,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}/accept",
        json=VALID_REQUEST,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "FIX_ACCEPTANCE_ERROR"


def test_get_accepted_fixes_history(monkeypatch):
    records = [
        {
            "id": FIX_ID,
            "upload_id": UPLOAD_ID,
            "file_path": "source.py",
            "rule_id": "PY004",
            "line": 3,
        }
    ]

    monkeypatch.setattr(
        fixes,
        "discover_python_files",
        lambda upload_id: [],
    )

    monkeypatch.setattr(
        fixes,
        "list_accepted_fixes",
        lambda upload_id: records,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted"
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["total"] == 1
    assert response.json()["accepted_fixes"] == records


def test_get_accepted_fixes_invalid_upload():
    response = client.get(
        "/api/v1/fix/invalid-id/accepted"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_get_accepted_fix_success(monkeypatch, tmp_path):
    accepted_root = (
        tmp_path / "data" / "accepted_fixes" / UPLOAD_ID
    )

    accepted_directory = accepted_root / FIX_ID
    accepted_directory.mkdir(parents=True)

    accepted_file = accepted_directory / "accepted.py"

    accepted_code = (
        "try:\n"
        "    risky_operation()\n"
        "except Exception:\n"
        "    pass\n"
    )

    accepted_file.write_text(
        accepted_code,
        encoding="utf-8",
    )

    record = {
        "id": FIX_ID,
        "upload_id": UPLOAD_ID,
        "file_path": "source.py",
        "rule_id": "PY004",
        "line": 3,
        "accepted_path": str(
            accepted_file.relative_to(tmp_path)
        ),
    }

    monkeypatch.setattr(
        fixes,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        fixes,
        "get_accepted_fix",
        lambda fix_id: record,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/{FIX_ID}"
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["accepted_code"] == accepted_code


def test_get_accepted_fix_invalid_fix_id():
    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/invalid-id"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_FIX_ID"


def test_get_accepted_fix_not_found(monkeypatch):
    monkeypatch.setattr(
        fixes,
        "get_accepted_fix",
        lambda fix_id: None,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/{FIX_ID}"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ACCEPTED_FIX_NOT_FOUND"


def test_get_accepted_fix_from_another_project(monkeypatch):
    record = {
        "id": FIX_ID,
        "upload_id": "c" * 32,
        "accepted_path": "data/accepted_fixes/other/accepted.py",
    }

    monkeypatch.setattr(
        fixes,
        "get_accepted_fix",
        lambda fix_id: record,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/{FIX_ID}"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ACCEPTED_FIX_NOT_FOUND"


def test_get_accepted_fix_rejects_path_traversal(monkeypatch, tmp_path):
    record = {
        "id": FIX_ID,
        "upload_id": UPLOAD_ID,
        "accepted_path": "../outside.py",
    }

    monkeypatch.setattr(
        fixes,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        fixes,
        "get_accepted_fix",
        lambda fix_id: record,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/{FIX_ID}"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_ACCEPTED_FILE_PATH"


def test_get_accepted_fix_missing_file(monkeypatch, tmp_path):
    accepted_root = (
        tmp_path / "data" / "accepted_fixes" / UPLOAD_ID
    )

    accepted_root.mkdir(parents=True)

    record = {
        "id": FIX_ID,
        "upload_id": UPLOAD_ID,
        "accepted_path": (
            f"data/accepted_fixes/{UPLOAD_ID}/{FIX_ID}/accepted.py"
        ),
    }

    monkeypatch.setattr(
        fixes,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        fixes,
        "get_accepted_fix",
        lambda fix_id: record,
    )

    response = client.get(
        f"/api/v1/fix/{UPLOAD_ID}/accepted/{FIX_ID}"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ACCEPTED_FILE_NOT_FOUND"