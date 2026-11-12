import pytest
from app.db.database import get_connection, initialize_database
from app.repositories.test_execution_repository import (
    get_latest_test_execution,
    get_test_execution_by_id,
    list_test_executions,
    save_test_execution,
)


@pytest.fixture
def execution_db(tmp_path):
    db_path = tmp_path / "test_execution.db"

    initialize_database(db_path)

    connection = get_connection(db_path)

    connection.execute(
        """
        INSERT INTO projects (
            upload_id,
            original_filename,
            upload_type
        )
        VALUES (?, ?, ?)
        """,
        ("a" * 32, "example.py", "python"),
    )

    connection.commit()
    connection.close()

    return db_path


@pytest.fixture
def sample_result():
    return {
        "success": True,
        "status": "passed",
        "exit_code": 0,
        "tests_total": 3,
        "passed": 3,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration_seconds": 0.25,
    }


def test_save_test_execution(
    execution_db,
    sample_result,
):
    execution = save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    assert execution is not None
    assert execution["upload_id"] == "a" * 32
    assert execution["result"] == sample_result


def test_get_test_execution_by_id(
    execution_db,
    sample_result,
):
    saved = save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    execution = get_test_execution_by_id(
        saved["id"],
        execution_db,
    )

    assert execution is not None
    assert execution["id"] == saved["id"]
    assert execution["result"] == sample_result


def test_get_latest_test_execution(
    execution_db,
    sample_result,
):
    first = save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    second_result = {
        **sample_result,
        "success": False,
        "status": "failed",
        "failed": 1,
    }

    second = save_test_execution(
        "a" * 32,
        second_result,
        execution_db,
    )

    latest = get_latest_test_execution(
        "a" * 32,
        execution_db,
    )

    assert latest["id"] == second["id"]
    assert latest["id"] != first["id"]
    assert latest["result"]["status"] == "failed"


def test_list_test_executions(
    execution_db,
    sample_result,
):
    save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    executions = list_test_executions(
        "a" * 32,
        execution_db,
    )

    assert len(executions) == 2


def test_missing_execution_returns_none(execution_db):
    execution = get_test_execution_by_id(
        999,
        execution_db,
    )

    assert execution is None


def test_empty_execution_history(execution_db):
    executions = list_test_executions(
        "a" * 32,
        execution_db,
    )

    assert executions == []


def test_latest_execution_returns_none(execution_db):
    execution = get_latest_test_execution(
        "a" * 32,
        execution_db,
    )

    assert execution is None


def test_execution_history_cascades_on_project_delete(
    execution_db,
    sample_result,
):
    save_test_execution(
        "a" * 32,
        sample_result,
        execution_db,
    )

    connection = get_connection(execution_db)

    connection.execute(
        "DELETE FROM projects WHERE upload_id = ?",
        ("a" * 32,),
    )

    connection.commit()
    connection.close()

    assert list_test_executions(
        "a" * 32,
        execution_db,
    ) == []