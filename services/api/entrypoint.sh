#!/bin/bash
set -e

echo "⏳ Waiting for database to be ready..."

until python -c "
import psycopg2, os
psycopg2.connect(
    host=os.environ['DATABASE_HOST'],
    port=os.environ.get('DATABASE_PORT', '5432'),
    user=os.environ['DATABASE_USER'],
    password=os.environ['DATABASE_PASSWORD'],
    dbname=os.environ['DATABASE_NAME']
)
" 2>/dev/null; do
  echo "⏳ Database not ready, retrying in 2s..."
  sleep 2
done

echo "✅ Database ready!"
echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2