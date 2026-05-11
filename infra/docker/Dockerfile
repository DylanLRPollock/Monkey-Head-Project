ARG PYTHON_VERSION=3.13-bookworm
FROM python:${PYTHON_VERSION}

ARG HUEY_EXTRAS=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config \
    portaudio19-dev \
    libasound2-dev libasound2 libasound2-data libasound2-plugins \
    ca-certificates \
    libglib2.0-0 libdbus-1-3 libnss3 \
    libx11-6 libx11-xcb1 libxkbcommon-x11-0 \
    libxext6 libxi6 libxrender1 \
    libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
    libxcb-xfixes0 libxcb-xinerama0 \
    libgl1 libegl1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
 && if [ -n "$HUEY_EXTRAS" ]; then \
      pip install --no-cache-dir ".[${HUEY_EXTRAS}]"; \
    else \
      pip install --no-cache-dir .; \
    fi

RUN useradd -m -u 1000 hueyos \
 && chown -R hueyos:hueyos /app

USER hueyos

EXPOSE 1995

ENTRYPOINT ["huey-api"]
