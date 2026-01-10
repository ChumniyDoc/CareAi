FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos "" appuser
WORKDIR /app

COPY pyproject.toml /app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[test]

COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY scripts /app/scripts

USER appuser

CMD ["bash", "/app/scripts/run_local.sh"]
