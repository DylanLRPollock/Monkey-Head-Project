#!/bin/bash
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.05.2025
# ==================================================
set -e

# Stop and remove compose services
if [ -f docker-compose.yml ]; then
    docker-compose down
fi

# Remove dangling images
docker image prune -f
# Remove unused volumes
docker volume prune -f
