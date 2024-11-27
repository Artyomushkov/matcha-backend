#!/bin/bash

# Navigate to the project directory
cd /home/jamatchaserver/matcha-backend

# Pull the latest code from the repository
git pull

# Rebuild and recreate the Docker service
docker-compose up -d --build --force-recreate matcha