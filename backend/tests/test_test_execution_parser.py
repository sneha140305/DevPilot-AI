from app.services.test_execution_service import parse_pytest_results


def test_parse_all_passed_tests():
    result = parse_pytest_results(
        ".. [100%]\n2 passed in 0.04s",
        "",
    )

    assert result["tests_total"] == 2
    assert result["passed"] == 2
    assert result["failed"] == 0
    assert result["duration_seconds"] == 0.04
    assert result["summary_available"] is True


def test_parse_failed_and_passed_tests():
    result = parse_pytest_results(
        "FAILED test_app.py::test_add - AssertionError\n"
        "1 failed, 2 passed in 0.50s",
        "",
    )

    assert result["tests_total"] == 3
    assert result["passed"] == 2
    assert result["failed"] == 1
    assert len(result["failure_details"]) == 1


def test_parse_skipped_and_error_tests():
    result = parse_pytest_results(
        "1 passed, 1 skipped, 1 error in 1.25s",
        "",
    )

    assert result["tests_total"] == 3
    assert result["passed"] == 1
    assert result["skipped"] == 1
    assert result["errors"] == 1


def test_parse_xfailed_and_xpassed():
    result = parse_pytest_results(
        "1 xfailed, 1 xpassed in 0.20s",
        "",
    )

    assert result["tests_total"] == 2
    assert result["xfailed"] == 1
    assert result["xpassed"] == 1


def test_parse_empty_output():
    result = parse_pytest_results("", "")

    assert result["tests_total"] == 0
    assert result["summary_available"] is False
    assert result["duration_seconds"] is None


def test_parse_output_with_summary_in_stderr():
    result = parse_pytest_results(
        "",
        "2 passed in 0.10s",
    )

    assert result["passed"] == 2
    assert result["summary_available"] is True