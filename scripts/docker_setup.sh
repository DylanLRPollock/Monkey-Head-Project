#!/bin/bash
set -e

# Build Docker image
docker build -t monkey-head-project:latest .

# Start services using docker-compose
if [ -f docker-compose.yml ]; then
    docker-compose up -d
fi

docker ps
