# syntax=docker/dockerfile:1.7

# "Full" (non-slim) default. Override at build time if you want slim:
#   docker build --build-arg PYTHON_VERSION=3.13-slim -t hueyos .
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION} AS hueyos

# Optional extras from pyproject.toml, e.g.:
#   docker build --build-arg HUEY_EXTRAS="dev,gpu" -t hueyos:extras .
ARG HUEY_EXTRAS=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HUEY_API_PORT=1995 \
    HUEY_HOST=0.0.0.0 \
    HUEY_CONFIG_DIR=/app/config \
    HUEY_MEMORY_DIR=/app/memory

WORKDIR /app

# Install build tooling once so the actual dependency install can reuse the cached layer.
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-bootstrap,sharing=locked \
    python -m pip install --upgrade pip setuptools wheel

COPY README.md pyproject.toml ./
COPY src ./src

# Install HueyOS with optional extras controlled by the build argument.
# (Cache mount provides speed; no --no-cache-dir so pip can actually reuse it.)
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-install,sharing=locked \
    if [ -n "${HUEY_EXTRAS}" ]; then \
        python -m pip install ".[${HUEY_EXTRAS}]"; \
    else \
        python -m pip install .; \
    fi

# Non-root execution user for better container security.
# Create runtime dirs BEFORE switching user, and ensure /app is writable.
RUN useradd --create-home --shell /bin/bash huey \
    && mkdir -p "${HUEY_CONFIG_DIR}" "${HUEY_MEMORY_DIR}" \
    && chown -R huey:huey /app

USER huey

# Runtime directories usually bind-mounted when running with Compose.
VOLUME ["/app/config", "/app/memory"]

EXPOSE 1995

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import os, socket; port = int(os.environ.get('HUEY_API_PORT', '1995')); s = socket.create_connection(('127.0.0.1', port), 2); s.close()"

# Use sh -c + exec so env vars are honored and signals propagate correctly.
CMD ["sh", "-c", "exec python -m uvicorn huey.api:app --host \"$HUEY_HOST\" --port \"$HUEY_API_PORT\""]