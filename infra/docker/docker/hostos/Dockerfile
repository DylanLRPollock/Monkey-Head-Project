# syntax=docker/dockerfile:1.7
# HostOS toolbox image
# `forky` is intentional here to track Debian testing for development-oriented helper images.
FROM debian:forky-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg \
      python3 python3-pip python3-venv \
      iproute2 iputils-ping dnsutils \
      git jq sudo nano vim less \
      ufw \
    && rm -rf /var/lib/apt/lists/*

# Optional: kubectl (latest stable)
RUN curl -fsSL https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl

# Create app user
ARG APP_USER=hostos
RUN useradd -m -s /bin/bash ${APP_USER} \
    && usermod -aG sudo ${APP_USER} \
    && echo "${APP_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-hostos

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Copy application
COPY hostos.py /app/hostos.py

# Default environment
ENV HOSTOS_PATH=/home/${APP_USER}/HostOS

# Switch to non-root
USER ${APP_USER}

# Helpful default command prints usage; override at run time
CMD ["python3", "/app/hostos.py", "--help"]
