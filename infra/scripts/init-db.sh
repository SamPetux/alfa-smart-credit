#!/sh
set -eu
echo "init-db: waiting for database…"
# psycopg connection retry is in Python seed/alembic; short sleep for first boot
sleep 2
echo "init-db: alembic upgrade head"
cd /app/backend
PYTHONPATH=/app alembic upgrade head
echo "init-db: seed"
PYTHONPATH=/app python -m backend.app.identity.seed
echo "init-db: done"
