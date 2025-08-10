# syntax=docker/dockerfile:1.7
# NanoOS image (lightweight worker)
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg \
      python3 python3-pip python3-venv \
      iproute2 iputils-ping dnsutils \
      git jq sudo nano vim less \
    && rm -rf /var/lib/apt/lists/*

ARG APP_USER=nanoos
RUN useradd -m -s /bin/bash ${APP_USER} \
    && usermod -aG sudo ${APP_USER} \
    && echo "${APP_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-nanoos

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt

COPY NanoOS.py /app/NanoOS.py

ENV NANOOS_PATH=/home/${APP_USER}/NanoOS

USER ${APP_USER}

CMD ["python3", "/app/NanoOS.py", "--help"]
