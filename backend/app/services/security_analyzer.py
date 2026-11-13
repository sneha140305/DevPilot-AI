import ast
import re

SECRET_NAME_PATTERN = re.compile(
    r"(password|passwd|secret|api[_-]?key|access[_-]?token)",
    re.IGNORECASE,
)

PLACEHOLDER_VALUES = {
    "",
    "password",
    "your_password",
    "your_api_key",
    "your_secret",
    "changeme",
    "change_me",
    "example",
    "test",
    "none",
    "null",
    "xxx",
}


class SecurityAnalyzer(ast.NodeVisitor):
    """Detect common Python security vulnerabilities using AST."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []

    def add_issue(
        self,
        rule_id: str,
        message: str,
        node: ast.AST,
        suggestion: str,
    ):
        self.issues.append({
            "rule_id": rule_id,
            "message": message,
            "file_path": self.filename,
            "line": getattr(node, "lineno", 1),
            "column": getattr(node, "col_offset", 0),
            "suggestion": suggestion,
        })

    def visit_Assign(self, node: ast.Assign):
        """Detect possible hardcoded credentials."""

        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id

                if SECRET_NAME_PATTERN.search(name):
                    value = node.value

                    if (
                        isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                    ):
                            normalized = value.value.strip().lower()

                            if (
                                normalized not in PLACEHOLDER_VALUES
                                and len(normalized) >= 4
                            ):
                                self.add_issue(
                                    "SEC001",
                                    "Possible hardcoded secret detected.",
                                    node,
                                    "Use environment variables or a "
                                    "secure secrets manager.",
                                )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect risky function calls."""

        function_name = ""

        if isinstance(node.func, ast.Name):
            function_name = node.func.id

        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr

        # SEC002: Potential SQL injection.
        if function_name in {"execute", "executemany"} and node.args:
                query = node.args[0]

                if isinstance(
                    query,
                    (ast.JoinedStr, ast.BinOp),
                ):
                    self.add_issue(
                        "SEC002",
                        "Potential SQL injection through "
                        "string formatting.",
                        node,
                        "Use parameterized SQL queries instead "
                        "of string interpolation.",
                    )

                elif (
                    isinstance(query, ast.Call)
                    and isinstance(query.func, ast.Attribute)
                    and query.func.attr == "format"
                ):
                    self.add_issue(
                        "SEC002",
                        "Potential SQL injection through "
                        "string formatting.",
                        node,
                        "Use parameterized SQL queries.",
                    )

        # SEC003: Shell execution.
        if function_name in {
            "run",
            "Popen",
            "call",
            "check_call",
            "check_output",
        }:
            shell_enabled = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )

            if shell_enabled:
                self.add_issue(
                    "SEC003",
                    "Shell execution with shell=True detected.",
                    node,
                    "Avoid shell=True. Pass commands as a list "
                    "of arguments and validate user input.",
                )

        # SEC004: Unsafe pickle deserialization.
        if function_name in {"loads", "load"}:
            module_name = ""

            if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                ):
                    module_name = node.func.value.id

            if module_name == "pickle":
                self.add_issue(
                    "SEC004",
                    "Potentially unsafe pickle deserialization.",
                    node,
                    "Do not deserialize untrusted data with pickle. "
                    "Use a safer serialization format.",
                )

        # SEC005: Weak hashing algorithms.
        if function_name in {"md5", "sha1"}:
            module_name = ""

            if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                ):
                    module_name = node.func.value.id

            if module_name == "hashlib":
                self.add_issue(
                    "SEC005",
                    f"Weak cryptographic hash detected: "
                    f"{function_name}.",
                    node,
                    "Use SHA-256 or a stronger algorithm "
                    "for security-sensitive hashing.",
                )

        self.generic_visit(node)


def analyze_security(source_code: str, filename: str):
    """
    Analyze Python source code for common security risks.

    This function parses source code but never executes it.
    """

    try:
        syntax_tree = ast.parse(
            source_code,
            filename=filename,
        )

    except SyntaxError:
        return []

    analyzer = SecurityAnalyzer(filename)
    analyzer.visit(syntax_tree)

    return analyzer.issues