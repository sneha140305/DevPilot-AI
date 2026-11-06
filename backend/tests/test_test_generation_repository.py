import pytest
from app.db.database import initialize_database
from app.repositories.project_repository import create_project
from app.repositories.test_generation_repository import (
    get_latest_test_generation,
    get_test_generation_by_id,
    list_test_generations,
    save_test_generation,
)


@pytest.fixture
def test_db(tmp_path):
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
def sample_result():
    return {
        "upload_id": "a" * 32,
        "file_path": "calculator.py",
        "total_functions": 2,
        "total_tests": 2,
        "success": True,
        "test_code": (
            "from calculator import add\n\n"
            "def test_add_exists():\n"
            "    assert callable(add)"
        ),
        "message": "Generated basic callable checks.",
    }


def test_save_test_generation(test_db, sample_result):
    result = save_test_generation(
        "a" * 32,
        sample_result,
        test_db,
    )

    assert result is not None
    assert result["upload_id"] == "a" * 32
    assert result["result"] == sample_result


def test_get_test_generation_by_id(test_db, sample_result):
    saved = save_test_generation(
        "a" * 32,
        sample_result,
        test_db,
    )

    result = get_test_generation_by_id(
        saved["id"],
        test_db,
    )

    assert result is not None
    assert result["result"] == sample_result


def test_get_latest_test_generation(test_db, sample_result):
    save_test_generation(
        "a" * 32,
        sample_result,
        test_db,
    )

    updated_result = {
        **sample_result,
        "total_tests": 5,
    }

    save_test_generation(
        "a" * 32,
        updated_result,
        test_db,
    )

    latest = get_latest_test_generation(
        "a" * 32,
        test_db,
    )

    assert latest is not None
    assert latest["result"]["total_tests"] == 5


def test_list_test_generations(test_db, sample_result):
    save_test_generation(
        "a" * 32,
        sample_result,
        test_db,
    )

    save_test_generation(
        "a" * 32,
        sample_result,
        test_db,
    )

    history = list_test_generations(
        "a" * 32,
        test_db,
    )

    assert len(history) == 2


def test_missing_test_generation(test_db):
    result = get_test_generation_by_id(
        999,
        test_db,
    )

    assert result is None


def test_empty_test_generation_history(test_db):
    history = list_test_generations(
        "a" * 32,
        test_db,
    )

    assert history == []