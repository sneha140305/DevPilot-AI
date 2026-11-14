# DevPilot AI

### AI-Powered Code Analysis, Debugging, and Testing Assistant
[![DevPilot AI CI](https://github.com/sneha140305/DevPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/sneha140305/DevPilot-AI/actions/workflows/ci.yml)
DevPilot AI is a developer-assistance project designed to analyze Python code, identify potential issues, explain findings, generate candidate unit tests, and propose reviewable code fixes.

The project combines deterministic static analysis with optional AI-assisted code review.

## Objectives

* Analyze Python source code using Python AST and Ruff.
* Identify syntax errors and supported code-quality issues.
* Generate AI-assisted explanations when an AI provider is configured.
* Produce structured analysis reports.
* Store analysis history in SQLite.
* Generate candidate Pytest tests.
* Propose code changes without automatically overwriting original source files.
* Provide a Streamlit dashboard.
* Support secure, testable software development practices.

## Technology Stack

* Python
* FastAPI
* Streamlit
* Python AST
* Ruff
* Pytest
* Pydantic
* SQLite
* Git and GitHub
* Optional Gemini API integration

## Project Status

**Current stage:** Phase 1 — Project Initialization.

Features will be documented as they are implemented and tested.

## Cost

The project is designed for local development using free and open-source software.

AI functionality is optional and may depend on the availability and limits of a free API tier. No paid API or cloud deployment is required for the initial setup.

## Planned Workflow

Upload → Validate → Analyze → Explain → Suggest Fix → Generate Tests → Verify → Human Approval

Test execution for uploaded code will remain disabled until an appropriate isolation mechanism is implemented and tested.

## Development Setup

### 1. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Review `.env.example` for the planned configuration.

Do not commit real API keys or other credentials.

### 4. Start the backend

The FastAPI application will be available after the backend implementation is completed.

Startup and testing instructions will be updated in the relevant development phase.

## Security

* Uploaded projects are untrusted input.
* ZIP archives must be validated before extraction.
* Secrets must not be committed.
* AI-generated findings are suggestions, not guaranteed diagnoses.
* Proposed code changes require review.
* Uploaded code must not be executed directly inside the backend process.

## Evaluation

The project will use controlled Python examples to evaluate analysis behavior. Metrics and test results will be reported only after they have actually been measured.

## License

This project is intended to use the MIT License. See the `LICENSE` file.
