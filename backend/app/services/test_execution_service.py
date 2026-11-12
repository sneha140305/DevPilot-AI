import re
import shutil
import subprocess
import threading
import uuid
from pathlib import Path

from app.core.config import PROJECT_ROOT
from app.repositories.test_execution_repository import (
    save_test_execution,
)
from app.repositories.test_generation_repository import (
    get_latest_test_generation,
)
from app.services.upload_service import UPLOAD_ROOT

DOCKER_IMAGE = "devpilot-test-runner:1.0"

EXECUTION_TIMEOUT = 30
DOCKER_CREATE_TIMEOUT = 10
DOCKER_CLEANUP_TIMEOUT = 5

MEMORY_LIMIT = "256m"
CPU_LIMIT = "0.5"
PID_LIMIT = "64"

MAX_OUTPUT_BYTES = 12_000
MAX_TEST_CODE_BYTES = 1_000_000

TEST_RUN_ROOT = PROJECT_ROOT / "data" / "test_runs"


class TestExecutionError(Exception):
    """Raised when secure test execution cannot be completed."""

    __test__ = False

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def validate_upload_id(upload_id: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise TestExecutionError(
            400,
            "INVALID_UPLOAD_ID",
            "Invalid upload ID.",
        )


def prepare_execution_workspace(
    upload_id: str,
    generation: dict,
) -> tuple[Path, str]:
    """
    Prepare a temporary copy of the uploaded source
    and the latest generated test.

    No uploaded code is executed here.
    """

    validate_upload_id(upload_id)

    upload_root = UPLOAD_ROOT.resolve()
    upload_directory = (UPLOAD_ROOT / upload_id).resolve()

    if not upload_directory.is_relative_to(upload_root):
        raise TestExecutionError(
            400,
            "INVALID_UPLOAD_PATH",
            "Invalid upload directory.",
        )

    if not upload_directory.is_dir():
        raise TestExecutionError(
            404,
            "UPLOAD_NOT_FOUND",
            "Uploaded project was not found.",
        )

    result = generation.get("result")

    if not isinstance(result, dict):
        raise TestExecutionError(
            400,
            "INVALID_TEST_GENERATION",
            "Generated test data is invalid.",
        )

    test_code = result.get("test_code", "")

    if not isinstance(test_code, str) or not test_code.strip():
        raise TestExecutionError(
            400,
            "NO_GENERATED_TESTS",
            "No generated test code is available.",
        )

    if len(test_code.encode("utf-8")) > MAX_TEST_CODE_BYTES:
        raise TestExecutionError(
            400,
            "TEST_CODE_TOO_LARGE",
            "Generated test code exceeds the allowed size.",
        )

    file_name = result.get("file_path", "")

    if (
        not isinstance(file_name, str)
        or not file_name
        or Path(file_name).name != file_name
        or Path(file_name).suffix.lower() != ".py"
    ):
        raise TestExecutionError(
            400,
            "INVALID_SOURCE_FILENAME",
            "Generated test references an invalid source file.",
        )

    single_file = upload_directory / "source.py"

    if single_file.is_file():
        source_file = single_file
        module_name = "source"
    else:
        project_directory = upload_directory / "project"

        source_file = (
            project_directory / file_name
        ).resolve()

        if not source_file.is_relative_to(
            project_directory.resolve()
        ):
            raise TestExecutionError(
                400,
                "INVALID_SOURCE_PATH",
                "Source file path is outside the project.",
            )

        module_name = source_file.stem

    if not source_file.is_file():
        raise TestExecutionError(
            404,
            "SOURCE_NOT_FOUND",
            "The source file required for testing was not found.",
        )

    expected_import = f"from {module_name} import "

    if expected_import not in test_code:
        raise TestExecutionError(
            400,
            "TEST_SOURCE_MISMATCH",
            "Generated tests do not match the uploaded source.",
        )

    TEST_RUN_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    workspace = (
        TEST_RUN_ROOT / uuid.uuid4().hex
    ).resolve()

    if not workspace.is_relative_to(TEST_RUN_ROOT.resolve()):
        raise TestExecutionError(
            400,
            "INVALID_WORKSPACE",
            "Execution workspace is outside the permitted directory.",
        )

    workspace.mkdir(
        parents=True,
        exist_ok=False,
    )

    try:
        destination = workspace / source_file.name

        shutil.copyfile(
            source_file,
            destination,
        )

        test_file = workspace / "test_devpilot_generated.py"

        test_file.write_text(
            test_code,
            encoding="utf-8",
        )

        return workspace, test_file.name

    except Exception:
        shutil.rmtree(
            workspace,
            ignore_errors=True,
        )
        raise


def _capture_bounded_output(
    stream,
    output_buffer: bytearray,
) -> None:
    """
    Continuously drain a process stream while retaining
    only the latest MAX_OUTPUT_BYTES.
    """

    while True:
        chunk = stream.read(4096)

        if not chunk:
            break

        output_buffer.extend(chunk)

        if len(output_buffer) > MAX_OUTPUT_BYTES:
            del output_buffer[:-MAX_OUTPUT_BYTES]


def _decode_output(output_buffer: bytearray) -> str:
    return bytes(output_buffer).decode(
        "utf-8",
        errors="replace",
    )
    
def parse_pytest_results(stdout: str, stderr: str) -> dict:
    """Extract structured test results from pytest output."""

    output = f"{stdout}\n{stderr}"

    result = {
        "tests_total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0,
        "duration_seconds": None,
        "summary_available": False,
        "failure_details": [],
    }

    count_pattern = re.compile(
        r"(\d+)\s+(passed|failed|skipped|errors?|xfailed|xpassed)"
    )

    for match in count_pattern.finditer(output):
        count = int(match.group(1))
        category = match.group(2)

        if category == "error":
            category = "errors"

        result[category] += count

    duration_match = re.search(
        r"in\s+(\d+(?:\.\d+)?)s",
        output,
    )

    if duration_match:
        result["duration_seconds"] = float(
            duration_match.group(1)
        )

    result["tests_total"] = sum(
        result[key]
        for key in (
            "passed",
            "failed",
            "skipped",
            "errors",
            "xfailed",
            "xpassed",
        )
    )

    result["summary_available"] = duration_match is not None

    for line in output.splitlines():
        stripped = line.strip()

        if stripped.startswith(("FAILED ", "ERROR ")):
            result["failure_details"].append(stripped)

    return result

def _cleanup_container(container_id: str) -> None:
    """
    Force-remove the container.

    This is called even when execution fails or times out.
    """

    try:
        subprocess.run(
            [
                "docker",
                "rm",
                "--force",
                container_id,
            ],
            capture_output=True,
            timeout=DOCKER_CLEANUP_TIMEOUT,
            check=False,
            shell=False,
        )
    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ):
        pass


def execute_tests_in_docker(
    workspace: Path,
    test_file_name: str,
) -> dict:
    """
    Execute generated tests inside a restricted Docker container.

    Uploaded code is never executed on the host.

    Container lifecycle:
        1. Create restricted container.
        2. Start and attach to its output.
        3. Enforce execution timeout.
        4. Kill on timeout.
        5. Remove container in all cases.
    """

    workspace = workspace.resolve()

    if not workspace.is_dir():
        raise TestExecutionError(
            400,
            "INVALID_WORKSPACE",
            "Execution workspace does not exist.",
        )

    if not workspace.is_relative_to(TEST_RUN_ROOT.resolve()):
        raise TestExecutionError(
            400,
            "INVALID_WORKSPACE",
            "Workspace is outside the permitted test directory.",
        )

    if (
        not test_file_name
        or Path(test_file_name).name != test_file_name
        or not test_file_name.startswith("test_")
        or not test_file_name.endswith(".py")
    ):
        raise TestExecutionError(
            400,
            "INVALID_TEST_FILE",
            "Invalid generated test filename.",
        )

    test_file = workspace / test_file_name

    if test_file.is_symlink() or not test_file.is_file():
        raise TestExecutionError(
            404,
            "TEST_FILE_NOT_FOUND",
            "Generated test file was not found.",
        )

    container_name = f"devpilot-test-{uuid.uuid4().hex[:12]}"

    # Create the container without executing uploaded code.
    create_command = [
        "docker",
        "create",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=16m",
        "--memory", MEMORY_LIMIT,
        "--memory-swap", MEMORY_LIMIT,
        "--cpus", CPU_LIMIT,
        "--pids-limit", str(PID_LIMIT),
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--mount",
        (
            f"type=bind,source={workspace.as_posix()},"
            "target=/workspace,readonly"
        ),
        "--workdir", "/workspace",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--env", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "--entrypoint", "python",
        DOCKER_IMAGE,
        "-m",
        "pytest",
        "-q",
        "-p", "no:cacheprovider",
        "--noconftest",
        "-c", "/dev/null",
        "--tb=short",
        test_file_name,
    ]

    container_id = None
    process = None

    stdout_buffer = bytearray()
    stderr_buffer = bytearray()

    try:
        created = subprocess.run(
            create_command,
            capture_output=True,
            text=True,
            timeout=DOCKER_CREATE_TIMEOUT,
            check=False,
            shell=False,
        )
       
        if created.returncode != 0:
            raise TestExecutionError(
                503,
                "DOCKER_CREATE_FAILED",
                "Docker could not create the test container.",
            )

        container_id = created.stdout.strip()

        if not container_id:
            raise TestExecutionError(
                503,
                "DOCKER_CREATE_FAILED",
                "Docker did not return a container ID.",
            )

        # Uploaded code starts executing only after this command.
        process = subprocess.Popen(
            [
                "docker",
                "start",
                "--attach",
                container_id,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        stdout_thread = threading.Thread(
            target=_capture_bounded_output,
            args=(process.stdout, stdout_buffer),
            daemon=True,
        )

        stderr_thread = threading.Thread(
            target=_capture_bounded_output,
            args=(process.stderr, stderr_buffer),
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()

        try:
            process.wait(timeout=EXECUTION_TIMEOUT)

        except subprocess.TimeoutExpired:
            try:
                subprocess.run(
                    [
                        "docker",
                        "kill",
                        container_id,
                    ],
                    capture_output=True,
                    timeout=DOCKER_CLEANUP_TIMEOUT,
                    check=False,
                    shell=False,
                )
            except (
                FileNotFoundError,
                subprocess.SubprocessError,
                OSError,
            ):
                pass

            try:
                process.wait(timeout=DOCKER_CLEANUP_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=DOCKER_CLEANUP_TIMEOUT)

            raise TestExecutionError(
                408,
                "TEST_EXECUTION_TIMEOUT",
                "Test execution exceeded the 30-second time limit.",
            )

        finally:
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)

        return_code = process.returncode

        if return_code == 0:
            status = "passed"
        elif return_code == 1:
            status = "failed"
        else:
            status = "error"

        return {
            "status": status,
            "exit_code": return_code,
            "stdout": _decode_output(stdout_buffer),
            "stderr": _decode_output(stderr_buffer),
        }

    except TestExecutionError:
        raise

    except FileNotFoundError as exc:
        raise TestExecutionError(
            503,
            "DOCKER_UNAVAILABLE",
            "Docker CLI is not available.",
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise TestExecutionError(
            503,
            "DOCKER_EXECUTION_ERROR",
            "Docker did not respond within the allowed time.",
        ) from exc

    except OSError as exc:
        raise TestExecutionError(
            503,
            "DOCKER_EXECUTION_ERROR",
            "Docker execution could not be completed.",
        ) from exc

    finally:
        if process is not None and process.poll() is None:
            process.kill()

            try:
                process.wait(timeout=DOCKER_CLEANUP_TIMEOUT)
            except subprocess.SubprocessError:
                pass

        if container_id:
            _cleanup_container(container_id)


def run_generated_tests(upload_id: str) -> dict:
    """
    Retrieve, prepare and execute the latest generated tests.
    """

    validate_upload_id(upload_id)

    generation = get_latest_test_generation(upload_id)

    if generation is None:
        raise TestExecutionError(
            404,
            "TEST_GENERATION_NOT_FOUND",
            "Generate tests before requesting execution.",
        )

    workspace = None

    try:
        workspace, test_file_name = prepare_execution_workspace(
            upload_id,
            generation,
        )

        execution = execute_tests_in_docker(
            workspace,
            test_file_name,
        )

        parsed_results = parse_pytest_results(
            execution["stdout"],
            execution["stderr"],
       )

        result ={
            "success": execution["status"] == "passed",
            "upload_id": upload_id,
            "status": execution["status"],
            "exit_code": execution["exit_code"],
            "stdout": execution["stdout"],
            "stderr": execution["stderr"],
            "test_file": test_file_name,
            **parsed_results,
        }

        save_test_execution(upload_id, result)
        return result
    
    finally:
        if workspace is not None:
            shutil.rmtree(
                workspace,
                ignore_errors=True,
            )
