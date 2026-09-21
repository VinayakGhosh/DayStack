echo "Update Alembic Head..."
alembic upgrade head

echo "Starting FastApi server..."
uvicorn main:app --host 0.0.0.0