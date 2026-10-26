# D06 — разработка и проверка backend

Часть комплекта сдачи, подготовленная Дмитрием по существующим скриптам Олега. Полная приёмка D06 открыта: frontend — заглушка, E01 до выдачи не реализован; независимый чистый запуск и техническое подтверждение владельцем ещё нужны.

## Запуск

Из корня checkout на машине с Docker и Compose v2:

```bash
docker compose up --build -d
docker compose ps -a
docker compose logs --tail 80 init api worker
```

Ожидается успешный init (exit 0), здоровая БД и работающие api/worker/web/proxy. Это штатная команда проекта, но её запуск без дополнительных настроек облачной среды здесь не подтверждён. При первой сборке нужна сеть для пакетов и образов. Штатный Compose не публикует БД наружу.

В подготовленной облачной среде нужны поправки для доверенного CA прокси, прав файлов 0600 и внутренних соединений Caddy. Они сохранены при onboarding вне Git, в `/workspace/shared/alfa-onboarding/`. Только для этой среды:

```bash
bash /workspace/shared/alfa-onboarding/install.sh
export COMPOSE_FILE=compose.yaml:/workspace/shared/alfa-onboarding/compose.yaml
bash /workspace/shared/alfa-onboarding/start.sh
```

Эти helper-файлы не входят в репозиторий; при обычном clone они отсутствуют. Не отключать TLS-проверку для обхода ошибки сертификата. Исправление штатной инфраструктуры передать Олегу, а не менять её в продуктовой задаче.

Для локальной разработки без контейнера API: Python 3.12+, PostgreSQL 16, виртуальное окружение и `pip install -e './backend[dev]'` из корня. В облачной среде уже есть `.venv`; зависимости установлены через uv. Локальные migrations и worker используют один и тот же DATABASE_URL. Команды из README выполняются из backend с PYTHONPATH, указывающим на корень. Один `.env` сам по себе не гарантирует загрузку переменных: перед запуском они должны быть экспортированы в процесс.

## Конфигурация

| Переменная | Назначение и граница |
|---|---|
| DATABASE_URL | Соединение backend/worker/init с PostgreSQL; тестам нужна отдельная БД |
| DEMO_MODE, APP_ENV | Демо-профили и маркировка окружения; не выдавать demo за production |
| SESSION_SECRET, SESSION_TTL_SECONDS | Параметры сессии; реальные секреты не коммитить |
| COOKIE_SECURE, SESSION_COOKIE_NAME | Cookie; локальный HTTP допускает COOKIE_SECURE=false, публичный HTTPS требует отдельной проверки |
| DOCUMENTS_DIR | Закрытое хранилище документов; backend и worker должны видеть одни данные |
| JOB_MAX_ATTEMPTS, JOB_LEASE_SECONDS, WORKER_POLL_SECONDS | Ограниченные повторы, lease и опрос очереди |

Источник имён и defaults — [.env.example](../.env.example) и [config.py](../backend/app/core/config.py). Предлагаемые архитектурой переменные не объявляются реализованными без проверки config.py. Демо-профили и тестовые пароли — [demo-accounts.md](demo-accounts.md); это синтетические аккаунты.

## Проверки без frontend

API проверяется локальными запросами: health/ready должен вернуть JSON со status=ok и миграцией (одного HTTP 200 недостаточно); demo session создаёт cookie и CSRF token; products возвращает два продукта. Submit требует актуальный expected_version, CSRF, Idempotency-Key и обязательные документы. Money в JSON — string. Документированные примеры — [contracts/examples](../contracts/examples/).

Unit-тесты из корня с установленной `.venv`:

```bash
.venv/bin/python -m pytest backend/tests/unit -q
```

Полный существующий набор backend-тестов внутри собранного API-образа на **новой выделенной тестовой БД**. Если работает облачный override, сначала экспортировать COMPOSE_FILE как выше. Не использовать БД живого demo: тесты создают фиксированные idempotency keys, а живой worker конкурировал бы с тестами worker.

```bash
test_db="alfa_test_$(date +%s)_${RANDOM}"
docker compose exec -T db createdb -U alfa "$test_db"
docker compose run --rm --no-deps \
  -e "DATABASE_URL=postgresql+psycopg://alfa:alfa@db:5432/$test_db" \
  -e DOCUMENTS_DIR=/tmp/alfa-test-documents \
  api python -m pytest /app/backend/tests -q
# После просмотра результата удалить только созданную выше тестовую БД:
docker compose exec -T db dropdb -U alfa "$test_db"
```

Проверять код завершения pytest до cleanup; успешный dropdb не означает успешные тесты. Для native pytest можно использовать БД с loopback-портом 55432 из облачного override. Повторять тесты на свежей БД.

В текущей работе документируется результат только реально выполненной команды. Предыдущая настройка среды дала 29 unit + 11 integration без пропусков и HTTP-сценарий до MANUAL_REVIEW. Ни этот результат, ни текущий набор тестов не являются полным E01–E16. Ограничения покрытия — [requirements.md](requirements.md).

В ходе D06 команда контейнерного pytest выше повторно выполнена на новой временной БД с облачным COMPOSE_FILE: **40 passed, 0 skipped, 1 warning, 3.73 s**. Предупреждение: Starlette TestClient сообщает о deprecated использовании httpx; зависимости в этой задаче не менялись. Созданная тестовая БД удалена после проверки. Исходная база кода — `72ba781`, среда Linux/amd64, PostgreSQL 16.6. Это подтверждение текущего запуска, не независимого clean clone.

## Остановка и диагностика (troubleshooting)

`docker compose stop` останавливает сервисы; `docker compose start` возобновляет существующие контейнеры. `docker compose down` удаляет контейнеры/сеть, сохраняя именованные volumes. Обычная остановка не должна сбрасывать заявки. Тест восстановления после аварии — отдельная задача QA (Q04).

| Симптом | Что смотреть |
|---|---|
| init exit ≠ 0 | `docker compose logs init db`; DATABASE_URL; не делать `down -v` ради «починить» |
| ready 503 | миграция/`alembic_version`, доступ api→db |
| TLS/CA при сборке в облаке | доверенный системный CA; не `--trusted-host` и не отключение проверки |
| Permission denied на documents | владелец volume/`DOCUMENTS_DIR`; образ создаёт `/data/documents` под appuser |
| 403 proxy / CORS | Caddyfile: `/api/*` → api; один origin 8080 |
| 401/403 API | сессия, роль, CSRF; чужая company → 404/403 |
| 409 VERSION_CONFLICT / STALE_RUN | перечитать заявку; не форсить decision |
| Заявка зависла в CHECKING | `jobs` state/attempts/`last_error`; worker logs; lease reclaim |
| SIGNED без COMPLETED | failed `simulate_disbursement`; officer `retry-disbursement` |
| Demo 404 | `DEMO_MODE=false` — ожидаемо; использовать `/auth/login` |
| OpenAPI CI red | `python scripts/check_openapi_contract.py` |

Разрушительный сброс: `docker compose down -v` удаляет БД и документы project — только после явного решения.

## Платформы (B11)

Зафиксировано при разработке backend: **macOS arm64**, локальный PostgreSQL 16, pytest unit/integration.  
GitHub Actions CI: **linux/amd64**. Compose smoke на agent-хосте часто без Docker. **arm64-контейнеры и второе окружение не прогнаны** — не заявлять multi-arch. Q05 — независимый замер.

## Что ещё нужно для D06 / сдачи

Полный E01 с UI; clean clone/Q05; digests образов; API-коллекция/Q06; полный notices; сданный tag без rewrite. Не production-ready.
