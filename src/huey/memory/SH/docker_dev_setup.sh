#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Docker Dev Setup shell script (huey/memory/SH)

set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.11.2025
# ==================================================
set -e

# Build Docker image
docker build -t monkey-head-project:latest .

# Start services using compose-dev.yaml
if [ -f compose-dev.yaml ]; then
    docker compose -f compose-dev.yaml up -d
fi

docker ps
