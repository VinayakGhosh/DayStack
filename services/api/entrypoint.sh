#!/bin/bash
set -e

echo "⏳ Waiting for database to be ready..."

until python -c "
import os
from sqlalchemy import create_engine
from db.config import resolve_database_url

engine = create_engine(resolve_database_url(os.environ))
with engine.connect():
    pass
engine.dispose()
" 2>/dev/null; do
  echo "⏳ Database not ready, retrying in 2s..."
  sleep 2
done

echo "✅ Database ready!"
echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
