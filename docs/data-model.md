# Модель данных (B02)

Канон сущностей — `docs/planning/02-architecture.md` §5. Реализация:

| Слой | Путь |
|---|---|
| ORM | `backend/app/db/models.py` |
| Миграции | `backend/migrations/` (Alembic) |
| DTO | `backend/app/schemas/` |
| OpenAPI | `contracts/openapi.yaml` |

## Инварианты P0

- UUID PK, время UTC (`timestamptz`), деньги `NUMERIC(18,2)`.
- Сырой session token не хранится — только `sessions.token_hash`.
- `version` / `revision` / `run_id` — разные поля.
- `UNIQUE(application_id)` на `disbursement_simulations`.
- `UNIQUE(actor_id, command_scope, idempotency_key)` на idempotency.
- Циклический FK `applications.active_run_id → evaluation_runs.id` создаётся после обеих таблиц.

## Миграции

```bash
export DATABASE_URL=postgresql+psycopg://alfa:alfa@127.0.0.1:5432/alfa_credit
cd backend && alembic upgrade head
```

Seed и демо-пользователи — задача **B03/B08**, не эта миграция.
