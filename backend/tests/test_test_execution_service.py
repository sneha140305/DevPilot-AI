import io
import subprocess

import pytest
from app.services import test_execution_service as service


@pytest.fixture
def uploaded_project(tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    upload_id = "a" * 32

    upload_directory = upload_root / upload_id
    upload_directory.mkdir(parents=True)

    source_file = upload_directory / "source.py"
    source_file.write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    test_run_root = tmp_path / "test_runs"

    monkeypatch.setattr(service, "UPLOAD_ROOT", upload_root)
    monkeypatch.setattr(service, "TEST_RUN_ROOT", test_run_root)

    generation = {
        "result": {
            "file_path": "example.py",
            "test_code": (
                "from source import add\n\n"
                "def test_add_exists():\n"
                "    assert callable(add)\n"
            ),
        }
    }

    return upload_id, generation, upload_directory


@pytest.fixture
def execution_workspace(tmp_path, monkeypatch):
    test_run_root = tmp_path / "test_runs"
    test_run_root.mkdir()

    monkeypatch.setattr(
        service,
        "TEST_RUN_ROOT",
        test_run_root,
    )

    workspace = test_run_root / "workspace"
    workspace.mkdir()

    test_file = workspace / "test_example.py"
    test_file.write_text(
        "def test_example():\n    assert True\n",
        encoding="utf-8",
    )

    return workspace, test_file


class FakeDockerProcess:
    """Simulate the Docker start --attach process."""

    def __init__(
        self,
        returncode=0,
        stdout=b"1 passed",
        stderr=b"",
    ):
        self.returncode = returncode
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode

    def kill(self):
        self.returncode = -9


def fake_docker_create_and_cleanup(command, **kwargs):
    """Simulate Docker create and rm commands."""

    if command[1] == "create":
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="container-123\n",
            stderr="",
        )

    if command[1] == "rm":
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="container-123",
            stderr="",
        )

    if command[1] == "kill":
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="container-123",
            stderr="",
        )

    raise AssertionError(f"Unexpected Docker command: {command}")


def test_validate_upload_id_rejects_invalid_id():
    with pytest.raises(service.TestExecutionError) as exc:
        service.validate_upload_id("../invalid")

    assert exc.value.status_code == 400
    assert exc.value.code == "INVALID_UPLOAD_ID"


def test_prepare_workspace_copies_source_and_tests(
    uploaded_project,
):
    upload_id, generation, upload_directory = uploaded_project

    workspace, test_file = service.prepare_execution_workspace(
        upload_id,
        generation,
    )

    try:
        assert workspace.is_dir()
        assert workspace.is_relative_to(
            service.TEST_RUN_ROOT.resolve()
        )

        assert (workspace / "source.py").is_file()
        assert (workspace / test_file).is_file()

        assert (
            workspace / "source.py"
        ).read_text(encoding="utf-8") == (
            upload_directory / "source.py"
        ).read_text(encoding="utf-8")

        assert "from source import add" in (
            workspace / test_file
        ).read_text(encoding="utf-8")

    finally:
        service.shutil.rmtree(workspace, ignore_errors=True)


def test_prepare_workspace_rejects_empty_test_code(
    uploaded_project,
):
    upload_id, generation, _ = uploaded_project
    generation["result"]["test_code"] = ""

    with pytest.raises(service.TestExecutionError) as exc:
        service.prepare_execution_workspace(
            upload_id,
            generation,
        )

    assert exc.value.code == "NO_GENERATED_TESTS"


def test_prepare_workspace_rejects_missing_source(
    uploaded_project,
):
    upload_id, generation, upload_directory = uploaded_project

    (upload_directory / "source.py").unlink()

    with pytest.raises(service.TestExecutionError) as exc:
        service.prepare_execution_workspace(
            upload_id,
            generation,
        )

    assert exc.value.code == "SOURCE_NOT_FOUND"


def test_docker_execution_passes_security_flags(
    execution_workspace,
    monkeypatch,
):
    workspace, test_file = execution_workspace
    docker_commands = []

    def fake_run(command, **kwargs):
        docker_commands.append(command)

        assert kwargs["shell"] is False

        if command[1] == "create":
            assert kwargs["timeout"] == service.DOCKER_CREATE_TIMEOUT

            assert "--network" in command
            assert "none" in command
            assert "--read-only" in command
            assert "--cap-drop" in command
            assert "ALL" in command
            assert "--pids-limit" in command
            assert "--memory" in command
            assert "--cpus" in command
            assert "--security-opt" in command
            assert "no-new-privileges" in command
            assert "--mount" in command
            assert any("readonly" in argument for argument in command)

            return subprocess.CompletedProcess(
                command,
                0,
                stdout="container-123",
                stderr="",
            )

        if command[1] == "rm":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(
        service.subprocess,
        "run",
        fake_run,
    )

    monkeypatch.setattr(
        service.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeDockerProcess(),
    )

    result = service.execute_tests_in_docker(
        workspace,
        test_file.name,
    )

    assert result["status"] == "passed"
    assert result["exit_code"] == 0
    assert "1 passed" in result["stdout"]

    assert any(command[1] == "create" for command in docker_commands)
    assert any(command[1] == "rm" for command in docker_commands)


def test_docker_execution_handles_failed_tests(
    execution_workspace,
    monkeypatch,
):
    workspace, test_file = execution_workspace

    monkeypatch.setattr(
        service.subprocess,
        "run",
        fake_docker_create_and_cleanup,
    )

    monkeypatch.setattr(
        service.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeDockerProcess(
            returncode=1,
            stdout=b"1 failed",
            stderr=b"AssertionError",
        ),
    )

    result = service.execute_tests_in_docker(
        workspace,
        test_file.name,
    )

    assert result["status"] == "failed"
    assert result["exit_code"] == 1
    assert "AssertionError" in result["stderr"]


def test_docker_execution_handles_timeout(
    execution_workspace,
    monkeypatch,
):
    workspace, test_file = execution_workspace

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)

        if command[1] == "create":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="container-123",
                stderr="",
            )

        return subprocess.CompletedProcess(
            command,
            0,
            stdout="",
            stderr="",
        )

    class TimeoutDockerProcess(FakeDockerProcess):
        def __init__(self):
            super().__init__()
            self.wait_calls = 0

        def wait(self, timeout=None):
            self.wait_calls += 1

            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired(
                    "docker start",
                    service.EXECUTION_TIMEOUT,
                )

            self.returncode = -9
            return self.returncode

    monkeypatch.setattr(
        service.subprocess,
        "run",
        fake_run,
    )

    monkeypatch.setattr(
        service.subprocess,
        "Popen",
        lambda *args, **kwargs: TimeoutDockerProcess(),
    )

    with pytest.raises(service.TestExecutionError) as exc:
        service.execute_tests_in_docker(
            workspace,
            test_file.name,
        )

    assert exc.value.status_code == 408
    assert exc.value.code == "TEST_EXECUTION_TIMEOUT"

    assert any(command[1] == "kill" for command in calls)
    assert any(command[1] == "rm" for command in calls)


def test_docker_execution_handles_unavailable_docker(
    execution_workspace,
    monkeypatch,
):
    workspace, test_file = execution_workspace

    def fake_run(command, **kwargs):
        raise FileNotFoundError("Docker not found")

    monkeypatch.setattr(
        service.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(service.TestExecutionError) as exc:
        service.execute_tests_in_docker(
            workspace,
            test_file.name,
        )

    assert exc.value.status_code == 503
    assert exc.value.code == "DOCKER_UNAVAILABLE"


def test_bounded_output_retains_only_latest_bytes():
    output = bytearray()

    service._capture_bounded_output(
        io.BytesIO(b"A" * (service.MAX_OUTPUT_BYTES + 5000)),
        output,
    )

    assert len(output) == service.MAX_OUTPUT_BYTES
    assert output == bytearray(b"A" * service.MAX_OUTPUT_BYTES)


def test_output_decoding_handles_invalid_utf8():
    output = bytearray(b"Hello \xff World")

    decoded = service._decode_output(output)

    assert "Hello" in decoded
    assert "World" in decoded


def test_execution_rejects_workspace_outside_test_root(
    tmp_path,
    monkeypatch,
):
    test_run_root = tmp_path / "test_runs"

    monkeypatch.setattr(
        service,
        "TEST_RUN_ROOT",
        test_run_root,
    )

    workspace = tmp_path / "outside"
    workspace.mkdir()

    test_file = workspace / "test_example.py"
    test_file.write_text("", encoding="utf-8")

    with pytest.raises(service.TestExecutionError) as exc:
        service.execute_tests_in_docker(
            workspace,
            test_file.name,
        )

    assert exc.value.code == "INVALID_WORKSPACE"


def test_run_generated_tests_cleans_workspace(
    uploaded_project,
    monkeypatch,
):
    upload_id, generation, _ = uploaded_project
    saved_executions = []

    monkeypatch.setattr(
        service,
        "get_latest_test_generation",
        lambda upload_id: generation,
    )

    monkeypatch.setattr(
        service,
        "execute_tests_in_docker",
        lambda workspace, test_file: {
            "status": "passed",
            "exit_code": 0,
            "stdout": "1 passed in 0.04s",
            "stderr": "",
        },
    )

    monkeypatch.setattr(
        service,
        "save_test_execution",
        lambda saved_upload_id, result: saved_executions.append(
            (saved_upload_id, result)
        ),
    )

    result = service.run_generated_tests(upload_id)

    assert result["success"] is True
    assert result["status"] == "passed"
    assert result["upload_id"] == upload_id

    # Verify execution history persistence was called.
    assert len(saved_executions) == 1
    assert saved_executions[0][0] == upload_id
    assert saved_executions[0][1]["status"] == "passed"

    # Verify temporary workspace cleanup.
    assert not list(service.TEST_RUN_ROOT.glob("*"))