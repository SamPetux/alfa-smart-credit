# alfa-smart-credit

Умный кредитный кабинет — учебный веб-прототип (клиент + сотрудник банка) на синтетических данных.

> Backend P0 (B01–B11) + frontend F01–F10 в Compose (сборка `Dockerfile.web`).  
> Шаблонные объяснения: `GET /api/v1/applications/{id}/explain` (без LLM).  
> Ещё нет: git tag сдачи, независимый E01/E2E QA (Рамазан).  
> **Не** production-ready и **не** соответствие банковским регуляторным требованиям.

## Документы

| Путь | Содержание |
|---|---|
| [AGENTS.md](./AGENTS.md) | Правила для ИИ и команды |
| [docs/architecture.md](./docs/architecture.md) | As-built архитектура (B11) |
| [docs/api.md](./docs/api.md) | Руководство API v1 |
| [docs/states.md](./docs/states.md) | State machine |
| [docs/data-model.md](./docs/data-model.md) | ORM, ER, миграции |
| [docs/planning/](./docs/planning/) | Задание, целевая архитектура, роли |
| [docs/adr/001-modular-monolith.md](./docs/adr/001-modular-monolith.md) | Выбор стека |
| [contracts/](./contracts/) | API v1, статусы, risk-v1, policy-v1 |
| [docs/risk.md](./docs/risk.md) | Реализация score/policy/affordability |
| [docs/demo-accounts.md](./docs/demo-accounts.md) | Демо-профили и тестовые пароли |
| [docs/backend-development.md](./docs/backend-development.md) | Конфиг, проверки, troubleshooting |
| [docs/release.md](./docs/release.md) | Tag/SHA, digests (B10) |
| [docs/ai-explanations.md](./docs/ai-explanations.md) | Объяснения: шаблоны vs open-weight LLM |
| [docs/product.md](./docs/product.md) | JTBD, P0/P1 (Дима) |
| [docs/backlog.md](./docs/backlog.md) | Задания и блокеры |
| [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) | Предварительный реестр зависимостей |
| [.github/workflows/ci.yml](./.github/workflows/ci.yml) | CI pipeline |

## Стек

- Frontend: React + TypeScript + Vite (Игорь, F01–F10; `frontend/package-lock.json`)
- Backend / worker: Python 3.12 + FastAPI + SQLAlchemy + Alembic (Олег)
- Risk: чистый Python-модуль без сети/БД (Илья)
- PostgreSQL 16, Compose, один origin через Caddy

## Контракты G0

- Статусы: `contracts/statuses.json` → `docs/states.md`
- OpenAPI: `contracts/openapi.yaml` (+ `openapi.json` snapshot)
- Risk / policy: `contracts/schemas/`
- Примеры: `contracts/examples/`

## Запуск

```bash
docker compose up --build -d
# один origin: http://127.0.0.1:8080
sh infra/scripts/smoke-origin.sh
```

Compose: `db` → `init` → `api`/`worker` → `web` → `proxy`. Volumes: `pgdata`, `documents`. БД не публикуется.

Локально без Docker: см. [backend-development.md](./docs/backend-development.md). Аккаунты: [demo-accounts.md](./docs/demo-accounts.md).

```bash
pip install -e './backend[dev]'
ruff check backend/app
PYTHONPATH=. pytest backend/tests/unit -q
DATABASE_URL=… PYTHONPATH=. pytest backend/tests/integration -q
PYTHONPATH=. python scripts/check_openapi_contract.py
```

## Ограничения платформ

- Dev + Compose smoke: **macOS arm64** (Docker Desktop), `sh infra/scripts/smoke-origin.sh` — OK (2026-10-26).  
- CI: **linux/amd64**. Отдельный прогон Compose на amd64 — через GitHub Actions `compose-smoke`.  
- Подробности: [architecture.md](./docs/architecture.md#платформы), digests — [release.md](./docs/release.md).

## Роли

- **Дима** — продукт · **Игорь** — frontend · **Олег** — backend/архитектура · **Илья** — risk · **Рамазан** — QA  

Инструкции: `docs/planning/roles/`.
