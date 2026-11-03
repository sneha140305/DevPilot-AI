from app.services.test_generator import (
    extract_function_metadata,
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