# alfa-smart-credit

Умный кредитный кабинет — учебный веб-прототип (клиент + сотрудник банка) на синтетических данных.

> До B06: черновик → worker → MANUAL_REVIEW → уточнение/approve/reject. B07 (accept/sign) ещё нет.

## Документы

| Путь | Содержание |
|---|---|
| [AGENTS.md](./AGENTS.md) | Правила для ИИ и команды |
| [docs/planning/](./docs/planning/) | Задание, архитектура, роли |
| [docs/adr/001-modular-monolith.md](./docs/adr/001-modular-monolith.md) | Выбор стека |
| [contracts/](./contracts/) | API v1, статусы, risk-v1, policy-v1 |
| [docs/risk.md](./docs/risk.md) | Реализация score/policy/affordability |
| [docs/data-model.md](./docs/data-model.md) | ORM и миграции (B02) |
| [docs/demo-accounts.md](./docs/demo-accounts.md) | Демо-профили и тестовые пароли (B03) |
| [docs/product.md](./docs/product.md) | JTBD, границы P0/P1 и критерии успеха (D01/D02) |
| [docs/backlog.md](./docs/backlog.md) | Задания, зависимости и блокеры (D04) |
| [docs/requirements.md](./docs/requirements.md) | Фактическое покрытие R01–R18 и пробелы (D05) |
| [docs/backend-development.md](./docs/backend-development.md) | Backend-проверки, конфигурация и ограничения запуска (часть D06) |
| [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) | Предварительный реестр зависимостей; комплект лицензий ещё не завершён |

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

## Запуск

```bash
docker compose up --build
# UI/API: http://127.0.0.1:8080  (proxy → api + web placeholder)
```

Compose: `db` → `init` (alembic + idempotent seed) → `api` / `worker` → `web` → `proxy`.  
Frontend — заглушка до Fxx Игоря. Worker обрабатывает jobs: симуляторы + risk, успешный путь до MANUAL_REVIEW. Банковские решения и завершение полного E01 ещё отсутствуют.

Для этой облачной среды нужны дополнительные настройки CA и прав файлов, сохранённые вне Git при onboarding. Штатный запуск без них здесь не подтверждён; подробности и проверенные команды — в [инструкции backend](./docs/backend-development.md).

Локально без Docker:

```bash
export DATABASE_URL=postgresql+psycopg://…/alfa_credit
cd backend && alembic upgrade head && PYTHONPATH=.. python -m backend.app.identity.seed
PYTHONPATH=.. uvicorn backend.app.main:app --reload
# аккаунты: docs/demo-accounts.md
```

Тесты:

```bash
cd backend && PYTHONPATH=.. pytest tests/unit -q
DATABASE_URL=… PYTHONPATH=.. pytest tests/integration -q
```

## Роли

- **Дима** — продукт и координация  
- **Игорь** — frontend  
- **Олег** — backend, архитектура, контракты, infra  
- **Илья** — risk  
- **Рамазан** — QA / приёмка  

Инструкции ролей: `docs/planning/roles/`.
