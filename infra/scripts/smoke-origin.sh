#!/sh
# Дымовая проверка одного origin после `docker compose up --build`.
# Ожидает proxy на 127.0.0.1:8080.
set -eu
BASE="${SMOKE_BASE:-http://127.0.0.1:8080}"

echo "smoke: live"
curl -fsS "$BASE/api/v1/health/live" | grep -q '"status":"ok"'

echo "smoke: ready"
curl -fsS "$BASE/api/v1/health/ready" | grep -q '"status":"ok"'

echo "smoke: spa index"
html="$(curl -fsS "$BASE/")"
echo "$html" | grep -q '<div id="root">'
echo "$html" | grep -q '/assets/index-'
# SPA fallback для клиентского маршрута
curl -fsS "$BASE/demo" | grep -q '<div id="root">'

echo "smoke: ok (same origin UI+API)"
