FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PROJECT_DIR="/code"

ENV PATH="$POETRY_HOME/bin:$PROJECT_DIR/.venv/bin:$PATH"

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && chmod a+x /opt/poetry/bin/poetry

COPY pyproject.toml ./
RUN poetry install --no-root --only main,dev

COPY . .

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "5"]
