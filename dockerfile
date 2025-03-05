# Use Debian Trixie as base image
FROM debian:trixie

# Install system dependencies and Python 3.12
RUN apt update && apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/workspace/venv \
    PATH="/workspace/venv/bin:$PATH"

# Create workspace directory
WORKDIR /workspace

# Create and activate Python virtual environment
RUN python3.12 -m venv $VIRTUAL_ENV

# Install Python packages (assuming requirements.txt exists)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Ensure correct file permissions
RUN chown -R root:root /workspace

# Auto-activate virtual environment and launch interactive shell
CMD ["/bin/bash", "-c", "source $VIRTUAL_ENV/bin/activate && exec bash"]