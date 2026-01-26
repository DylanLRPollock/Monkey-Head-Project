# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13-slim
FROM python:${PYTHON_VERSION} AS hueyos

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
    pip install --upgrade pip setuptools wheel

COPY README.md pyproject.toml ./
COPY src ./src

# Install HueyOS with optional extras controlled by the build argument.
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-install,sharing=locked \
    if [ -n "${HUEY_EXTRAS}" ]; then \
        pip install --no-cache-dir ".[${HUEY_EXTRAS}]"; \
    else \
        pip install --no-cache-dir .; \
    fi

# Non-root execution user for better container security.
RUN useradd --create-home --shell /bin/bash huey
USER huey

# Runtime directories that are usually bind-mounted when running with Compose.
RUN mkdir -p "${HUEY_CONFIG_DIR}" "${HUEY_MEMORY_DIR}"
VOLUME ["/app/config", "/app/memory"]

EXPOSE 1995

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import os, socket; port = int(os.environ.get('HUEY_API_PORT', '1995')); s = socket.create_connection(('127.0.0.1', port), 2); s.close()"

ENTRYPOINT ["uvicorn"]
CMD ["huey.api:app", "--host", "0.0.0.0", "--port", "1995"]
