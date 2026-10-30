# DevPilot AI Architecture

## Overview

DevPilot AI uses a modular monolithic backend with a separate Streamlit frontend.

## Components

1. Streamlit frontend
2. FastAPI REST API
3. Upload and validation service
4. Python AST and Ruff static-analysis service
5. Optional Gemini AI-review service
6. Analysis and report service
7. SQLite persistence
8. Test-generation and patch services

## Data Flow

1. The user uploads a Python file or ZIP archive.
2. The backend validates the upload.
3. The static analyzer examines Python source files.
4. The optional AI service reviews source code.
5. The backend combines and labels findings.
6. The report is persisted and returned to the frontend.
7. The user can review findings and request candidate tests or fixes.

## Security Principles

- Treat uploads as untrusted input.
- Validate archive paths and file sizes.
- Keep API credentials outside version control.
- Separate deterministic findings from AI suggestions.
- Preserve original source code when proposing fixes.
- Do not execute arbitrary uploaded code inside the backend process.
- Enable test execution only after appropriate isolation has been implemented and tested.

## Current Status

This document describes the intended architecture. Components will be implemented and verified incrementally.
