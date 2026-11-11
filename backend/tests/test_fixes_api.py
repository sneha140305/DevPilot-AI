from app.api.routes import fixes
from app.main import app
from app.services.ast_analyzer import AnalysisError
from fastapi.testclient import TestClient

client = TestClient(app)

UPLOAD_ID = "a" * 32

VALID_REQUEST = {
    "file_path": "source.py",
    "rule_id": "PY004",
    "line": 3,
}

VALID_ANALYSIS = {
    "issues": [
        {
            "file_path": "source.py",
            "rule_id": "PY004",
            "line": 3,
        }
    ]
}

VALID_FIX = {
    "success": True,
    "supported": True,
    "message": "A proposed fix was generated and validated successfully.",
    "original_code": "try:\n    risky_operation()\nexcept:\n    pass\n",
    "proposed_code": (
        "try:\n    risky_operation()\nexcept Exception:\n    pass\n"
    ),
    "diff": "-except:\n+except Exception:\n",
    "validation_passed": True,
    "validation_message": "Proposed code passed Python AST syntax validation.",
}


def test_generate_fix_success(monkeypatch):
    monkeypatch.setattr(
        fixes,
        "analyze_project",
        lambda upload_id: VALID_ANALYSIS,
    )

    monkeypatch.setattr(
        fixes,
        "generate_fix",
        lambda **kwargs: VALID_FIX,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["supported"] is True
    assert data["validation_passed"] is True
    assert "except Exception:" in data["proposed_code"]


def test_generate_fix_unsupported_rule(monkeypatch):
    monkeypatch.setattr(
        fixes,
        "analyze_project",
        lambda upload_id: {
            "issues": [
                {
                    "file_path": "source.py",
                    "rule_id": "F401",
                    "line": 1,
                }
            ]
        },
    )

    monkeypatch.setattr(
        fixes,
        "generate_fix",
        lambda **kwargs: {
            "success": False,
            "supported": False,
            "message": "Automatic fixes are not yet supported.",
            "original_code": None,
            "proposed_code": None,
            "diff": None,
            "validation_passed": None,
            "validation_message": None,
        },
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json={
            "file_path": "source.py",
            "rule_id": "F401",
            "line": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["supported"] is False


def test_generate_fix_issue_not_found(monkeypatch):
    monkeypatch.setattr(
        fixes,
        "analyze_project",
        lambda upload_id: {"issues": []},
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json=VALID_REQUEST,
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ISSUE_NOT_FOUND"


def test_generate_fix_invalid_upload(monkeypatch):
    def raise_analysis_error(upload_id):
        raise AnalysisError(
            400,
            "INVALID_UPLOAD_ID",
            "Invalid upload ID.",
        )

    monkeypatch.setattr(
        fixes,
        "analyze_project",
        raise_analysis_error,
    )

    response = client.post(
        "/api/v1/fix/invalid-id",
        json=VALID_REQUEST,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_generate_fix_analysis_error(monkeypatch):
    def raise_analysis_error(upload_id):
        raise AnalysisError(
            404,
            "UPLOAD_NOT_FOUND",
            "Uploaded project was not found.",
        )

    monkeypatch.setattr(
        fixes,
        "analyze_project",
        raise_analysis_error,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json=VALID_REQUEST,
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UPLOAD_NOT_FOUND"


def test_generate_fix_invalid_request():
    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json={
            "file_path": "source.py",
            "rule_id": "PY004",
            "line": 0,
        },
    )

    assert response.status_code == 422


def test_generate_fix_preserves_original_source(monkeypatch):
    original_source = (
        "try:\n"
        "    risky_operation()\n"
        "except:\n"
        "    pass\n"
    )

    monkeypatch.setattr(
        fixes,
        "analyze_project",
        lambda upload_id: VALID_ANALYSIS,
    )

    def fake_generate_fix(**kwargs):
        return {
            **VALID_FIX,
            "original_code": original_source,
        }

    monkeypatch.setattr(
        fixes,
        "generate_fix",
        fake_generate_fix,
    )

    response = client.post(
        f"/api/v1/fix/{UPLOAD_ID}",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200
    assert response.json()["original_code"] == original_source