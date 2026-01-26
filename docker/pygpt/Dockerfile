FROM python:3.12-bookworm

# Qt/PySide runtime deps + a few common libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libglib2.0-0 libdbus-1-3 libnss3 \
    libx11-6 libx11-xcb1 libxkbcommon-x11-0 \
    libxext6 libxi6 libxrender1 \
    libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
    libxcb-xfixes0 libxcb-xinerama0 \
    libgl1 libegl1 \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user (optional but helps with mounted-volume permissions)
RUN useradd -m -u 1000 pygpt
USER pygpt
ENV HOME=/home/pygpt \
    QT_X11_NO_MITSHM=1

# Install PyGPT from PyPI
RUN python -m pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir pygpt-net

# PyGPT stores config/data in its workdir; we'll default to /data
ENTRYPOINT ["pygpt"]
CMD ["--workdir=/data"]
