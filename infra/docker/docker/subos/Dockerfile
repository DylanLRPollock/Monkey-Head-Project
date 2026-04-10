# Use Debian slim base image; release can be overridden at build time
ARG DEBIAN_RELEASE=trixie
FROM debian:${DEBIAN_RELEASE}-slim

# Define maintainer or author of the Dockerfile
LABEL maintainer="admin@subos.com"

# Set environment variables to minimize issues and configure Python not to create .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/dlrp

# Update the package repository and install necessary packages
# Using 'apt-get install -y --no-install-recommends' to keep the installation small
# Adding '&& apt-get clean' to remove unnecessary files and free space
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    mate-desktop-environment-core \
    tightvncserver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory inside the container
WORKDIR /subos-workdir

# Copy the project's requirements file first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies from the requirements file
# RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . .

# Non-root User:
# Correcting user creation and usage
RUN useradd -m dlrp && chown -R dlrp:dlrp /subos-workdir

# Add a startup wrapper that configures VNC auth from runtime env vars.
RUN cat <<'EOF' > /usr/local/bin/start-vnc.sh
#!/bin/bash
set -euo pipefail

if [ -z "${VNC_PASSWORD:-}" ]; then
    echo "ERROR: VNC_PASSWORD is required at runtime." >&2
    exit 1
fi

mkdir -p "$HOME/.vnc"
chmod 700 "$HOME/.vnc"
umask 077
printf '%s\n' "$VNC_PASSWORD" | vncpasswd -f > "$HOME/.vnc/passwd"
chmod 600 "$HOME/.vnc/passwd"
unset VNC_PASSWORD

exec vncserver "$@"
EOF
RUN chmod +x /usr/local/bin/start-vnc.sh

USER dlrp

# Set up VNC server
RUN mkdir -p "$HOME/.vnc"

# Set up VNC session startup script
RUN echo "#!/bin/bash\nxrdb $HOME/.Xresources\nstartmate &" > "$HOME/.vnc/xstartup"
RUN chmod +x "$HOME/.vnc/xstartup"

# Expose the necessary port(s)
EXPOSE 5901

# Define the command to run when the container starts
CMD ["/usr/local/bin/start-vnc.sh", "-geometry", "1280x800", "-depth", "24", "-localhost", "no", ":1"]
