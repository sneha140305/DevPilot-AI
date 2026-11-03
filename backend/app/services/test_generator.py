import ast
from pathlib import Path
from typing import Any


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