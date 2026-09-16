#!/bin/bash

set -e

source .venv/Scripts/activate

echo "spinning up docker container to start database..."
docker compose up -d

echo "Update Alembic Head..."
alembic upgrade head

echo "Starting FastApi server..."
uvicorn main:app --reload