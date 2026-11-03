from app.services.test_generator import (
    extract_function_metadata,
    generate_test_code,
)


def test_discover_single_function():

    code = """
def add(a, b):
    return a + b
"""

    result = extract_function_metadata(code)

    assert result["success"] is True
    assert result["total_functions"] == 1
    assert result["functions"][0]["name"] == "add"


def test_discover_function_parameters():

    code = """
def greet(name, message="Hello"):
    return message + name
"""

    result = extract_function_metadata(code)

    parameters = result["functions"][0]["parameters"]

    assert parameters[0]["name"] == "name"
    assert parameters[0]["required"] is True

    assert parameters[1]["name"] == "message"
    assert parameters[1]["default"] == "'Hello'"
    assert parameters[1]["required"] is False


def test_discover_multiple_functions():

    code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

    result = extract_function_metadata(code)

    assert result["total_functions"] == 2


def test_detect_async_function():

    code = """
async def fetch_data(url):
    return url
"""

    result = extract_function_metadata(code)

    function = result["functions"][0]

    assert function["is_async"] is True


def test_detect_return_statement():

    code = """
def display():
    print("Hello")
"""

    result = extract_function_metadata(code)

    assert result["functions"][0]["has_return"] is False


def test_invalid_python_syntax():

    code = """
def add(a, b)
    return a + b
"""

    result = extract_function_metadata(code)

    assert result["success"] is False
    assert result["total_functions"] == 0


def test_discover_class_method():

    code = """
class Calculator:

    def add(self, a, b):
        return a + b
"""

    result = extract_function_metadata(code)

    function = result["functions"][0]

    assert function["name"] == "add"
    assert function["qualified_name"] == "Calculator.add"


def test_keyword_only_arguments():

    code = """
def connect(host, *, timeout=10):
    return host
"""

    result = extract_function_metadata(code)

    parameters = result["functions"][0]["parameters"]

    assert parameters[1]["name"] == "timeout"
    assert parameters[1]["kind"] == "keyword_only"
    assert parameters[1]["default"] == "10"


def test_generate_basic_pytest_code():

    metadata = extract_function_metadata(
        """
def add(a, b):
    return a + b
"""
    )

    result = generate_test_code(metadata, "calculator")

    assert result["success"] is True
    assert result["total_tests"] == 1
    assert "from calculator import add" in result["test_code"]
    assert "def test_add_exists():" in result["test_code"]


def test_generate_tests_for_multiple_functions():

    metadata = extract_function_metadata(
        """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    )

    result = generate_test_code(metadata, "calculator")

    assert result["total_tests"] == 2
    assert "test_add_exists" in result["test_code"]
    assert "test_subtract_exists" in result["test_code"]


def test_skip_private_functions():

    metadata = extract_function_metadata(
        """
def _internal():
    return True

def public():
    return True
"""
    )

    result = generate_test_code(metadata, "sample")

    assert result["total_tests"] == 1
    assert "_internal" not in result["test_code"]


def test_skip_async_functions():

    metadata = extract_function_metadata(
        """
async def fetch():
    return True
"""
    )

    result = generate_test_code(metadata, "sample")

    assert result["total_tests"] == 0


def test_reject_invalid_module_name():

    metadata = extract_function_metadata(
        """
def add(a, b):
    return a + b
"""
    )

    import pytest

    with pytest.raises(ValueError):
        generate_test_code(metadata, "invalid-module")


def test_no_functions_found():

    metadata = extract_function_metadata(
        """
x = 10
y = 20
"""
    )

    result = generate_test_code(metadata, "sample")

    assert result["success"] is True
    assert result["total_tests"] == 0