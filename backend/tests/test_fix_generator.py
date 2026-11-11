import pytest
from app.services.ast_analyzer import AnalysisError
from app.services.fix_generator import generate_fix, validate_python_source


def create_uploaded_project(
    tmp_path,
    monkeypatch,
    source_code,
):
    from app.services import upload_service

    upload_id = "a" * 32

    project_directory = tmp_path / upload_id
    project_directory.mkdir()

    source_file = project_directory / "source.py"

    source_file.write_text(
        source_code,
        encoding="utf-8",
    )

    monkeypatch.setattr(
        upload_service,
        "UPLOAD_ROOT",
        tmp_path,
    )

    return upload_id, source_file


def test_generate_bare_except_fix(tmp_path, monkeypatch):
    source = (
        "try:\n"
        "    result = 10 / value\n"
        "except:\n"
        "    print('Error')\n"
    )

    upload_id, source_file = create_uploaded_project(
        tmp_path,
        monkeypatch,
        source,
    )

    result = generate_fix(
        upload_id=upload_id,
        file_path="source.py",
        rule_id="RUFF-E722",
        line=3,
    )

    assert result["success"] is True
    assert result["supported"] is True

    assert "except Exception:" in result["proposed_code"]

    assert "-except:" in result["diff"]
    assert "+except Exception:" in result["diff"]

    # Original file must remain unchanged.
    assert source_file.read_text(encoding="utf-8") == source


def test_unsupported_rule(tmp_path, monkeypatch):
    source = "print('Hello')\n"

    upload_id, _ = create_uploaded_project(
        tmp_path,
        monkeypatch,
        source,
    )

    result = generate_fix(
        upload_id=upload_id,
        file_path="source.py",
        rule_id="RUFF-F401",
        line=1,
    )

    assert result["success"] is False
    assert result["supported"] is False


def test_invalid_line(tmp_path, monkeypatch):
    source = "try:\n    pass\nexcept:\n    pass\n"

    upload_id, _ = create_uploaded_project(
        tmp_path,
        monkeypatch,
        source,
    )

    with pytest.raises(ValueError):
        generate_fix(
            upload_id=upload_id,
            file_path="source.py",
            rule_id="PY004",
            line=100,
        )


def test_invalid_file_path(tmp_path, monkeypatch):
    source = "print('Hello')\n"

    upload_id, _ = create_uploaded_project(
        tmp_path,
        monkeypatch,
        source,
    )

    with pytest.raises(AnalysisError) as exc_info:
        generate_fix(
            upload_id=upload_id,
            file_path="../outside.py",
            rule_id="PY004",
            line=1,
       )

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "SOURCE_FILE_NOT_FOUND"


def test_validate_valid_python_source():
    source = """
def calculate(a, b):
    return a + b
"""

    result = validate_python_source(source)

    assert result["valid"] is True
    assert "passed" in result["message"]


def test_validate_invalid_python_source():
    source = """
def calculate(a, b)
    return a + b
"""

    result = validate_python_source(source)

    assert result["valid"] is False
    assert "Syntax error" in result["message"]


def test_generated_fix_passes_ast_validation(
    tmp_path,
    monkeypatch,
):
    upload_id, _ = create_uploaded_project(
        tmp_path,
        monkeypatch,
        "try:\n    risky_operation()\nexcept:\n    pass\n",
    )

    result = generate_fix(
        upload_id=upload_id,
        file_path="source.py",
        rule_id="PY004",
        line=3,
    )

    assert result["success"] is True
    assert result["validation_passed"] is True
    assert result["proposed_code"] is not None