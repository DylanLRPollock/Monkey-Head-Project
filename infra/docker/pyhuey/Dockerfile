FROM python:3.12-bookworm

# Optional PyHuey cockpit/tooling image derived from upstream PyGPT runtime.
# This image is intentionally separate from the HueyOS runtime image.
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

RUN useradd -m -u 1000 pyhuey
USER pyhuey
ENV HOME=/home/pyhuey \
    QT_X11_NO_MITSHM=1

# Preserve upstream provenance/compatibility by installing upstream package.
RUN python -m pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir pygpt-net

WORKDIR /workspace

# Keep upstream entrypoint for compatibility; PyHuey identity is documented as
# project-controlled cockpit/tooling integration surface.
ENTRYPOINT ["pygpt"]
CMD ["--workdir=/data"]
