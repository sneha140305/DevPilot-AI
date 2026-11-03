import ast
import re
from pathlib import Path
from typing import Any

from app.services.upload_service import UPLOAD_ROOT


def get_default_value(node: ast.expr) -> str:
    """Convert a default AST expression into readable source."""

    return ast.unparse(node)


def extract_function_metadata(
    source_code: str,
    file_path: str = "uploaded.py",
) -> dict[str, Any]:
    """
    Discover Python functions using AST.
    Uploaded source code is never executed.
    """

    try:
        tree = ast.parse(source_code)

    except SyntaxError as exc:
        return {
            "success": False,
            "file_path": file_path,
            "error": str(exc),
            "functions": [],
            "total_functions": 0,
        }

    functions = []

    class FunctionVisitor(ast.NodeVisitor):

        def __init__(self):
            self.class_stack = []

        def visit_ClassDef(self, node: ast.ClassDef):
            self.class_stack.append(node.name)

            for child in node.body:
                self.visit(child)

            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self.process_function(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self.process_function(node)
            self.generic_visit(node)

        def process_function(self, node):

            arguments = node.args

            positional_args = (
                arguments.posonlyargs + arguments.args
            )

            defaults = [None] * (
                len(positional_args) - len(arguments.defaults)
            ) + arguments.defaults

            parameters = []

            for argument, default in zip(
                positional_args,
                defaults,
            ):
                parameters.append({
                    "name": argument.arg,
                    "default": (
                        get_default_value(default)
                        if default is not None
                        else None
                    ),
                    "required": default is None,
                    "kind": "positional",
                })

            for argument, default in zip(
                arguments.kwonlyargs,
                arguments.kw_defaults,
            ):
                parameters.append({
                    "name": argument.arg,
                    "default": (
                        get_default_value(default)
                        if default is not None
                        else None
                    ),
                    "required": default is None,
                    "kind": "keyword_only",
                })

            has_return = any(
                isinstance(child, ast.Return)
                for child in ast.walk(node)
            )

            functions.append({
                "name": node.name,
                "qualified_name": ".".join(
                    self.class_stack + [node.name]
                ),
                "parameters": parameters,
                "has_return": has_return,
                "is_async": isinstance(
                    node,
                    ast.AsyncFunctionDef,
                ),
                "line": node.lineno,
                "end_line": node.end_lineno,
            })

    visitor = FunctionVisitor()
    visitor.visit(tree)

    return {
        "success": True,
        "file_path": file_path,
        "total_functions": len(functions),
        "functions": functions,
    }


def discover_functions(file_path: Path) -> dict[str, Any]:
    """
    Read a Python file and discover its functions.
    """

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Python file not found: {file_path}"
        )

    if file_path.suffix.lower() != ".py":
        raise ValueError("Only Python files are supported.")

    source_code = file_path.read_text(
        encoding="utf-8"
    )

    return extract_function_metadata(
        source_code,
        file_path.name,
    )

def generate_test_code(
    metadata: dict[str, Any],
    module_name: str,
) -> dict[str, Any]:
    """
    Generate conservative pytest templates from discovered functions.

    Generated tests are proposals. They are not executed here.
    """

    if not metadata.get("success"):
        return {
            "success": False,
            "error": "Cannot generate tests for invalid Python code.",
            "test_code": "",
            "total_tests": 0,
        }

    if not module_name.isidentifier():
        raise ValueError("Invalid Python module name.")

    functions = metadata.get("functions", [])

    if not functions:
        return {
            "success": True,
            "test_code": "",
            "total_tests": 0,
            "message": "No functions were discovered.",
        }

    imports = []
    test_functions = []

    for function in functions:
        if function["name"].startswith("_"):
            continue

        if "." in function["qualified_name"]:
            # Class methods require class construction and
            # instance setup, which this basic generator
            # does not infer yet.
            continue

        if function["is_async"]:
            # Async execution requires an appropriate test
            # environment and event-loop configuration.
            continue

        name = function["name"]

        imports.append(name)

        test_name = f"test_{name}_exists"

        test_functions.append(
            f"def {test_name}():\n"
            f"    assert callable({name})\n"
        )

    if not test_functions:
        return {
            "success": True,
            "test_code": "",
            "total_tests": 0,
            "message": "No supported functions were discovered.",
        }

    unique_imports = sorted(set(imports))

    import_statement = (
        f"from {module_name} import "
        + ", ".join(unique_imports)
    )

    test_code = (
        f"{import_statement}\n\n\n"
        + "\n".join(test_functions)
    )

    return {
        "success": True,
        "test_code": test_code,
        "total_tests": len(test_functions),
        "message": (
            "Generated basic callable checks. "
            "Behavioral assertions require additional specifications."
        ),
    }

def generate_tests_for_upload(
    upload_id: str,
    file_name: str,
) -> dict[str, Any]:

    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise ValueError("Invalid upload ID.")

    if (
        not file_name
        or Path(file_name).name != file_name
        or Path(file_name).suffix.lower() != ".py"
    ):
        raise ValueError("Invalid Python filename.")

    upload_directory = (
        UPLOAD_ROOT / upload_id
    ).resolve()

    upload_root = UPLOAD_ROOT.resolve()

    if not upload_directory.is_relative_to(upload_root):
        raise ValueError("Invalid upload path.")

    if not upload_directory.is_dir():
        raise FileNotFoundError("Upload not found.")

    source_file = upload_directory / "source.py"

    if not source_file.is_file():
        project_directory = upload_directory / "project"

        source_file = (
            project_directory / file_name
        ).resolve()

        if not source_file.is_relative_to(project_directory.resolve()):
            raise ValueError("Invalid project file path.")

        if not source_file.is_file():
            raise FileNotFoundError("Python file not found.")

    metadata = discover_functions(source_file)

    module_name = source_file.stem

    generated = generate_test_code(
        metadata,
        module_name,
    )

    return {
        "upload_id": upload_id,
        "file_path": file_name,
        "total_functions": metadata["total_functions"],
        "total_tests": generated["total_tests"],
        "success": generated["success"],
        "test_code": generated["test_code"],
        "message": generated.get("message", ""),
    }