import hashlib
import sqlite3

import pytest
from app.db.database import get_connection, initialize_database
from app.repositories.project_repository import create_project
from app.services import accepted_fix_service as service
from app.services import upload_service
from app.services.ast_analyzer import AnalysisError

UPLOAD_ID = "a" * 32

ORIGINAL_CODE = """def read_number(value):
    try:
        return int(value)
    except:
        return 0
"""


def create_test_project(tmp_path, monkeypatch):
    """Create an isolated uploaded project and temporary database."""

    # Temporary project upload directory
    uploads_root = tmp_path / "data" / "uploads"
    uploads_root.mkdir(parents=True, exist_ok=True)

    project_directory = uploads_root / UPLOAD_ID
    project_directory.mkdir(parents=True, exist_ok=True)

    source_path = project_directory / "source.py"
    source_path.write_text(ORIGINAL_CODE, encoding="utf-8")

    # Temporary database
    database_path = tmp_path / "data" / "test.db"
    initialize_database(db_path=database_path)

    create_project(
        upload_id=UPLOAD_ID,
        original_filename="source.py",
        upload_type="python",
        db_path=database_path,
    )

    # Redirect production paths to the temporary test directory
    accepted_fix_root = tmp_path / "data" / "accepted_fixes"

    monkeypatch.setattr(
        upload_service,
        "UPLOAD_ROOT",
        uploads_root,
    )

    monkeypatch.setattr(
        service,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        service,
        "ACCEPTED_FIX_ROOT",
        accepted_fix_root,
    )

    # Save accepted fixes into the temporary database
    original_save_function = service.save_accepted_fix

    def save_to_test_database(**kwargs):
        return original_save_function(
            **kwargs,
            db_path=database_path,
        )

    monkeypatch.setattr(
        service,
        "save_accepted_fix",
        save_to_test_database,
    )

    return source_path, database_path


def test_accept_fix_saves_separate_file(tmp_path, monkeypatch):
    source_path, _ = create_test_project(
        tmp_path,
        monkeypatch,
    )

    result = service.accept_proposed_fix(
        upload_id=UPLOAD_ID,
        file_path="source.py",
        rule_id="PY004",
        line=4,
    )

    accepted_path = tmp_path / result["accepted_path"]

    assert result["success"] is True
    assert accepted_path.exists()
    assert "except Exception:" in accepted_path.read_text(
        encoding="utf-8"
    )

    # Original uploaded source must remain unchanged
    assert source_path.read_text(encoding="utf-8") == ORIGINAL_CODE


def test_accept_fix_stores_correct_hashes(tmp_path, monkeypatch):
    source_path, _ = create_test_project(
        tmp_path,
        monkeypatch,
    )

    # Calculate hash from the actual original file bytes
    original_hash = hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest()

    result = service.accept_proposed_fix(
        UPLOAD_ID,
        "source.py",
        "PY004",
        4,
    )

    accepted_path = tmp_path / result["accepted_path"]

    accepted_hash = hashlib.sha256(
        accepted_path.read_bytes()
    ).hexdigest()

    assert result["original_sha256"] == original_hash
    assert result["accepted_sha256"] == accepted_hash
    assert original_hash != accepted_hash

    # Original file must remain unchanged
    assert hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest() == original_hash

    
def test_accept_fix_persists_database_record(tmp_path, monkeypatch):
    _, database_path = create_test_project(
        tmp_path,
        monkeypatch,
    )

    result = service.accept_proposed_fix(
        UPLOAD_ID,
        "source.py",
        "PY004",
        4,
    )

    with get_connection(database_path) as connection:
        record = connection.execute(
            """
            SELECT *
            FROM accepted_fixes
            WHERE id = ?
            """,
            (result["fix_id"],),
        ).fetchone()

    assert record is not None
    assert record["upload_id"] == UPLOAD_ID
    assert record["file_path"] == "source.py"
    assert record["rule_id"] == "PY004"
    assert record["line"] == 4


def test_accept_fix_preserves_original_hash(tmp_path, monkeypatch):
    source_path, _ = create_test_project(
        tmp_path,
        monkeypatch,
    )

    original_hash_before = hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest()

    service.accept_proposed_fix(
        UPLOAD_ID,
        "source.py",
        "PY004",
        4,
    )

    original_hash_after = hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest()

    assert original_hash_before == original_hash_after


def test_accept_fix_rejects_unsupported_rule(tmp_path, monkeypatch):
    create_test_project(tmp_path, monkeypatch)

    with pytest.raises(ValueError):
        service.accept_proposed_fix(
            UPLOAD_ID,
            "source.py",
            "PY999",
            4,
        )


def test_accept_fix_rejects_missing_source(tmp_path, monkeypatch):
    create_test_project(tmp_path, monkeypatch)

    source_path = (
        tmp_path
        / "data"
        / "uploads"
        / UPLOAD_ID
        / "source.py"
    )

    source_path.unlink()

    with pytest.raises(AnalysisError):
        service.accept_proposed_fix(
            UPLOAD_ID,
            "source.py",
            "PY004",
            4,
        )


def test_accept_fix_removes_file_if_database_fails(
    tmp_path,
    monkeypatch,
):
    create_test_project(tmp_path, monkeypatch)

    def fail_database(**kwargs):
        raise sqlite3.OperationalError(
            "Database unavailable"
        )

    monkeypatch.setattr(
        service,
        "save_accepted_fix",
        fail_database,
    )

    with pytest.raises(sqlite3.OperationalError):
        service.accept_proposed_fix(
            UPLOAD_ID,
            "source.py",
            "PY004",
            4,
        )

    accepted_root = (
        tmp_path
        / "data"
        / "accepted_fixes"
        / UPLOAD_ID
    )

    if accepted_root.exists():
        accepted_files = list(accepted_root.rglob("accepted.py"))
        assert accepted_files == []


def test_accept_fix_creates_unique_versions(tmp_path, monkeypatch):
    create_test_project(tmp_path, monkeypatch)

    first = service.accept_proposed_fix(
        UPLOAD_ID,
        "source.py",
        "PY004",
        4,
    )

    second = service.accept_proposed_fix(
        UPLOAD_ID,
        "source.py",
        "PY004",
        4,
    )

    assert first["fix_id"] != second["fix_id"]
    assert first["accepted_path"] != second["accepted_path"]

    first_path = tmp_path / first["accepted_path"]
    second_path = tmp_path / second["accepted_path"]

    assert first_path.exists()
    assert second_path.exists()