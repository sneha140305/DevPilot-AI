FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
ENV PIP_NO_CACHE_DIR=1

RUN useradd --create-home --uid 10001 runner

RUN pip install --no-cache-dir pytest==8.3.5

WORKDIR /workspace

USER runner

ENTRYPOINT ["python", "-m", "pytest"]
