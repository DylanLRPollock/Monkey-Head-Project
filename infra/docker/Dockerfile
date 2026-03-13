ARG PYTHON_VERSION=3.13-bookworm
FROM python:${PYTHON_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
    # build tooling for pip packages with C extensions (like PyAudio)
    build-essential pkg-config \
    # needed for PyAudio build: provides portaudio.h
    portaudio19-dev \
    # optional but helps with audio backends on Linux
    libasound2-dev libasound2 libasound2-data libasound2-plugins \
    # Qt / X11 runtime deps (PySide)
    ca-certificates \
    libglib2.0-0 libdbus-1-3 libnss3 \
    libx11-6 libx11-xcb1 libxkbcommon-x11-0 \
    libxext6 libxi6 libxrender1 \
    libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
    libxcb-xfixes0 libxcb-xinerama0 \
    libgl1 libegl1 \
 && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir pygpt-net==2.0.154

# (optional) run as non-root at runtime
RUN useradd -m -u 1000 pygpt && mkdir -p /data && chown -R pygpt:pygpt /data
USER pygpt

ENV QT_X11_NO_MITSHM=1
ENTRYPOINT ["pygpt"]
CMD ["--workdir=/data"]
