import logging

from fastapi import APIRouter, HTTPException

from app.repositories.test_execution_repository import (
    get_latest_test_execution,
    list_test_executions,
)
from app.schemas.test_execution import (
    TestExecutionHistoryResponse,
    TestExecutionRecord,
    TestExecutionResponse,
)
from app.services.test_execution_service import (
    TestExecutionError,
    run_generated_tests,
    validate_upload_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/execute-tests",
    tags=["Test Execution"],
)


def validate_request_upload_id(upload_id: str):
    try:
        validate_upload_id(upload_id)
    except TestExecutionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc


@router.post(
    "/{upload_id}",
    response_model=TestExecutionResponse,
)
def execute_project_tests(upload_id: str):
    try:
        return run_generated_tests(upload_id)

    except TestExecutionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except Exception as exc:
        logger.exception("Test execution failed.")

        raise HTTPException(
            status_code=500,
            detail={
                "code": "TEST_EXECUTION_ERROR",
                "message": "Unable to execute generated tests.",
            },
        ) from exc


@router.get(
    "/{upload_id}/history",
    response_model=TestExecutionHistoryResponse,
)
def get_execution_history(upload_id: str):
    validate_request_upload_id(upload_id)

    executions = list_test_executions(upload_id)

    return {
        "upload_id": upload_id,
        "total_executions": len(executions),
        "executions": executions,
    }


@router.get(
    "/{upload_id}/latest",
    response_model=TestExecutionRecord,
)
def get_latest_execution(upload_id: str):
    validate_request_upload_id(upload_id)

    execution = get_latest_test_execution(upload_id)

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TEST_EXECUTION_NOT_FOUND",
                "message": "No test execution history found.",
            },
        )

    return execution