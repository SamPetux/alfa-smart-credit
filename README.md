# alfa-smart-credit

Умный кредитный кабинет — учебный веб-прототип (клиент + сотрудник банка) на синтетических данных.

> Это каркас G0: структура, контракты и state machine. Полный сценарий ещё не реализован.

## Документы

| Путь | Содержание |
|---|---|
| [AGENTS.md](./AGENTS.md) | Правила для ИИ и команды |
| [docs/planning/](./docs/planning/) | Задание, архитектура, роли |
| [docs/adr/001-modular-monolith.md](./docs/adr/001-modular-monolith.md) | Выбор стека |
| [contracts/](./contracts/) | API v1, статусы, risk-v1, policy-v1 |

## Стек (зафиксировать версии после первой сборки)

- Frontend: React + TypeScript + Vite (владелец: Игорь)
- Backend / worker: Python 3.12 + FastAPI + SQLAlchemy + Alembic (владелец: Олег)
- Risk: чистый Python-модуль без сети/БД (владелец: Илья)
- PostgreSQL 16, Compose, один origin через Caddy

## Контракты G0

- Статусы и команды: `contracts/statuses.json`
- OpenAPI: `contracts/openapi.yaml`
- Risk in/out: `contracts/schemas/risk-v1.*.json`
- Policy: `contracts/schemas/policy-v1.json`
- Примеры: `contracts/examples/`

Python-зеркало: `backend/app/schemas/`, переходы: `backend/app/workflow/transitions.py`.

## Запуск (после B08)

```bash
docker compose up --build
# UI/API: http://127.0.0.1:8080
```

Сейчас Compose и Dockerfile — каркас; миграции/seed и frontend build ещё не подключены.

## Роли

- **Дима** — продукт и координация  
- **Игорь** — frontend  
- **Олег** — backend, архитектура, контракты, infra  
- **Илья** — risk  
- **Рамазан** — QA / приёмка  

Инструкции ролей: `docs/planning/roles/`.
