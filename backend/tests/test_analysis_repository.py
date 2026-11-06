from pathlib import Path

import pytest
from app.db.database import initialize_database
from app.repositories.analysis_repository import (
    get_analysis_by_id,
    get_latest_analysis,
    list_analyses,
    save_analysis,
)
from app.repositories.project_repository import create_project


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_devpilot.db"

    initialize_database(db_path)

    create_project(
        upload_id="a" * 32,
        original_filename="calculator.py",
        upload_type="python",
        db_path=db_path,
    )

    return db_path


@pytest.fixture
def sample_result() -> dict:
    return {
        "success": True,
        "upload_id": "a" * 32,
        "total_files": 1,
        "analyzed_files": 1,
        "total_issues": 2,
        "severity_counts": {
            "high": 1,
            "medium": 1,
            "low": 0,
        },
        "category_counts": {
            "security": 1,
            "correctness": 1,
        },
        "quality_score": 80,
        "files": [
            {
                "file_path": "calculator.py",
                "status": "parsed",
                "lines_of_code": 20,
                "issue_count": 2,
            }
        ],
        "issues": [],
    }


def test_save_analysis(test_db, sample_result):
    saved = save_analysis(
        "a" * 32,
        sample_result,
        test_db,
    )

    assert saved is not None
    assert saved["upload_id"] == "a" * 32
    assert saved["result"] == sample_result


def test_get_analysis_by_id(test_db, sample_result):
    saved = save_analysis(
        "a" * 32,
        sample_result,
        test_db,
    )

    retrieved = get_analysis_by_id(
        saved["id"],
        test_db,
    )

    assert retrieved["result"] == sample_result


def test_get_latest_analysis(test_db, sample_result):
    save_analysis(
        "a" * 32,
        sample_result,
        test_db,
    )

    updated_result = {
        **sample_result,
        "quality_score": 95,
    }

    save_analysis(
        "a" * 32,
        updated_result,
        test_db,
    )

    latest = get_latest_analysis(
        "a" * 32,
        test_db,
    )

    assert latest["result"]["quality_score"] == 95


def test_list_analyses(test_db, sample_result):
    save_analysis(
        "a" * 32,
        sample_result,
        test_db,
    )

    save_analysis(
        "a" * 32,
        sample_result,
        test_db,
    )

    history = list_analyses(
        "a" * 32,
        test_db,
    )

    assert len(history) == 2


def test_get_missing_analysis(test_db):
    result = get_latest_analysis(
        "a" * 32,
        test_db,
    )

    assert result is None