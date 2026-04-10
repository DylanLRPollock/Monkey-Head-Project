# Base: Python 3.12 on Debian Forky (good wheel coverage / stability)
FROM python:3.12-forky

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps:
# - build-essential/pkg-config/python3-dev: compile C extensions when wheels aren't available
# - portaudio19-dev: provides portaudio.h for PyAudio
# - ALSA libs: runtime + headers (PyAudio / audio stack)
# - Qt/X11 libs: needed for PySide6 "xcb" backend and general WebEngine stability
RUN apt-get update && apt-get install -y \
    ca-certificates curl git \
    build-essential pkg-config python3-dev \
    portaudio19-dev \
    libasound2 libasound2-dev libasound2-data libasound2-plugins \
    libglib2.0-0 libdbus-1-3 libnss3 \
    libx11-6 libx11-xcb1 libxkbcommon-x11-0 \
    libxext6 libxi6 libxrender1 \
    libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
    libxcb-xfixes0 libxcb-xinerama0 \
    libgl1 libegl1 \
    # WebEngine/Chromium libs that commonly surface as missing .so
    libxcomposite1 libxdamage1 libxrandr2 libxss1 libxtst6 \
    libfontconfig1 libfreetype6 \
 && rm -rf /var/lib/apt/lists/*

# Install PyGPT
RUN python -m pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir pygpt-net

# Create non-root runtime user and persistent workdir
RUN useradd -m -u 1000 pygpt \
 && mkdir -p /data \
 && chown -R pygpt:pygpt /data

USER pygpt
WORKDIR /home/pygpt

# Container-friendly Qt setting
ENV QT_X11_NO_MITSHM=1

ENTRYPOINT ["pygpt"]
CMD ["--workdir=/data"]
