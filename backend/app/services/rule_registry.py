RULE_REGISTRY = {
    "PY001": {
        "name": "Python Syntax Error",
        "severity": "high",
        "category": "correctness",
        "confidence": 1.0,
        "suggestion": "Correct the Python syntax before running the program.",
    },
    "PY002": {
        "name": "Dangerous eval Usage",
        "severity": "high",
        "category": "security",
        "confidence": 0.95,
        "suggestion": (
            "Avoid eval(). Use safer alternatives such as "
            "ast.literal_eval() when evaluating Python literals."
        ),
    },
    "PY003": {
        "name": "Dynamic Code Execution",
        "severity": "high",
        "category": "security",
        "confidence": 0.95,
        "suggestion": (
            "Avoid exec() with dynamic or untrusted input. "
            "Use explicitly defined functions instead."
        ),
    },
    "PY004": {
        "name": "Bare Except",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 1.0,
        "suggestion": (
            "Catch specific exceptions instead of using bare except."
        ),
    },
    "PY005": {
        "name": "Wildcard Import",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 1.0,
        "suggestion": (
            "Import only the specific names required by your program."
        ),
    },
    "RUFF-F401": {
        "name": "Unused Import",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 0.95,
        "suggestion": "Remove the unused import.",
    },
    "RUFF-F821": {
        "name": "Undefined Name",
        "severity": "high",
        "category": "correctness",
        "confidence": 0.95,
        "suggestion": (
            "Check whether the variable or function is declared "
            "or imported correctly."
        ),
    },
    "RUFF-F841": {
        "name": "Unused Variable",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 0.95,
        "suggestion": "Remove the unused variable or use it appropriately.",
    },
    "RUFF-E501": {
        "name": "Line Too Long",
        "severity": "low",
        "category": "style",
        "confidence": 1.0,
        "suggestion": "Break the long line into shorter, readable lines.",
    },
    "RUFF-E722": {
        "name": "Bare Except",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 1.0,
        "suggestion": (
            "Catch specific exceptions instead of using bare except."
        ),
    },
    "RUFF-F811": {
        "name": "Redefined Unused Name",
        "severity": "medium",
        "category": "correctness",
        "confidence": 0.95,
        "suggestion": "Rename or remove the duplicate definition.",
    },

        "SEC001": {
        "name": "Hardcoded Secret",
        "severity": "high",
        "category": "security",
        "confidence": 0.90,
        "suggestion": (
            "Store credentials in environment variables "
            "or a secure secrets manager."
        ),
    },
    "SEC002": {
        "name": "Potential SQL Injection",
        "severity": "high",
        "category": "security",
        "confidence": 0.85,
        "suggestion": (
            "Use parameterized SQL queries instead of "
            "dynamic string construction."
        ),
    },
    "SEC003": {
        "name": "Unsafe Shell Execution",
        "severity": "high",
        "category": "security",
        "confidence": 0.95,
        "suggestion": (
            "Avoid shell=True and pass commands as "
            "a list of arguments."
        ),
    },
    "SEC004": {
        "name": "Unsafe Deserialization",
        "severity": "high",
        "category": "security",
        "confidence": 0.95,
        "suggestion": (
            "Avoid deserializing untrusted data with pickle."
        ),
    },
    "SEC005": {
        "name": "Weak Cryptographic Hash",
        "severity": "medium",
        "category": "security",
        "confidence": 0.95,
        "suggestion": (
            "Use SHA-256 or a stronger cryptographic "
            "hashing algorithm."
        ),
    },
        "CQ001": {
        "name": "High Cyclomatic Complexity",
        "severity": "medium",
        "category": "maintainability",
        "confidence": 0.90,
        "suggestion": (
            "Reduce branching complexity by extracting smaller "
            "functions and simplifying conditional logic."
        ),
    },

    "CQ002": {
        "name": "Long Function",
        "severity": "low",
        "category": "maintainability",
        "confidence": 0.95,
        "suggestion": (
            "Split long functions into smaller functions "
            "with clear responsibilities."
        ),
    },

    "CQ003": {
        "name": "Potential Duplicate Code",
        "severity": "low",
        "category": "maintainability",
        "confidence": 0.75,
        "suggestion": (
            "Consider extracting repeated logic into a reusable "
            "function or module."
        ),
    },
}


DEFAULT_RULE = {
    "name": "General Code Quality Issue",
    "severity": "low",
    "category": "style",
    "confidence": 0.70,
    "suggestion": "Review this finding and improve the affected code.",
}