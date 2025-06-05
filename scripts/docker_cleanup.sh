#!/bin/bash
set -e

# Stop and remove compose services
if [ -f docker-compose.yml ]; then
    docker-compose down
fi

# Remove dangling images
docker image prune -f
# Remove unused volumes
docker volume prune -f
