FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Packaging metadata + package source.
COPY pyproject.toml README.md ./
COPY src ./src

# Migrations: the container runs `alembic upgrade head` on start (see
# docker-compose.yml), so the migration environment must be present.
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["uvicorn", "oe_infrastructure.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]