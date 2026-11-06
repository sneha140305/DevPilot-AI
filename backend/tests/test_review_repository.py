
import pytest
from app.db.database import initialize_database
from app.repositories.project_repository import create_project
from app.repositories.review_repository import (
    get_latest_review,
    get_review_by_id,
    list_reviews,
    save_review,
)


@pytest.fixture
def database(tmp_path):
    db_path = tmp_path / "test_devpilot.db"

    initialize_database(db_path)

    create_project(
        upload_id="a" * 32,
        original_filename="test.py",
        upload_type="python",
        db_path=db_path,
    )

    return db_path


def sample_review():
    return {
        "upload_id": "a" * 32,
        "total_issues": 1,
        "review_provider": "rule_based",
        "reviews": [
            {
                "rule_id": "RUFF-F401",
                "severity": "medium",
                "message": "Unused import detected.",
                "fix_suggestion": "Remove the unused import.",
            }
        ],
    }


def test_save_review(database):
    result = save_review(
        upload_id="a" * 32,
        result=sample_review(),
        db_path=database,
    )

    assert result is not None
    assert result["upload_id"] == "a" * 32
    assert result["result"]["total_issues"] == 1


def test_get_review_by_id(database):
    saved = save_review(
        upload_id="a" * 32,
        result=sample_review(),
        db_path=database,
    )

    result = get_review_by_id(
        saved["id"],
        db_path=database,
    )

    assert result is not None
    assert result["id"] == saved["id"]


def test_get_latest_review(database):
    first = sample_review()

    second = sample_review()
    second["total_issues"] = 3

    save_review(
        upload_id="a" * 32,
        result=first,
        db_path=database,
    )

    latest = save_review(
        upload_id="a" * 32,
        result=second,
        db_path=database,
    )

    result = get_latest_review(
        "a" * 32,
        db_path=database,
    )

    assert result is not None
    assert result["id"] == latest["id"]
    assert result["result"]["total_issues"] == 3


def test_list_reviews(database):
    save_review(
        upload_id="a" * 32,
        result=sample_review(),
        db_path=database,
    )

    save_review(
        upload_id="a" * 32,
        result=sample_review(),
        db_path=database,
    )

    results = list_reviews(
        "a" * 32,
        db_path=database,
    )

    assert len(results) == 2


def test_get_missing_review(database):
    result = get_review_by_id(
        999,
        db_path=database,
    )

    assert result is None