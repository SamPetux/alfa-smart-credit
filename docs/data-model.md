# Модель данных (B02 / B11)

Канон сущностей: [planning/02-architecture.md](planning/02-architecture.md) §5. Реализация:

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
- `UNIQUE(application_id)` на `disbursement_simulations` (одна имитация выдачи).
- `UNIQUE(actor_id, command_scope, idempotency_key)` на idempotency.
- Циклический FK `applications.active_run_id → evaluation_runs.id` после обеих таблиц.
- Audit append-only на уровне приложения (не юридически неизменяемый журнал).

## ER (ядро)

```mermaid
erDiagram
  COMPANY ||--o{ MEMBERSHIP : has
  USER ||--o{ MEMBERSHIP : has
  COMPANY ||--o{ APPLICATION : owns
  PRODUCT ||--o{ APPLICATION : for
  APPLICATION ||--o{ APPLICATION_REVISION : versions
  APPLICATION ||--o{ DOCUMENT : uploads
  APPLICATION ||--o{ EVALUATION_RUN : runs
  EVALUATION_RUN ||--o| RISK_ASSESSMENT : result
  EVALUATION_RUN ||--o{ INTEGRATION_CHECK : checks
  APPLICATION ||--o{ DECISION : officer
  DECISION ||--o| OFFER : creates
  OFFER ||--o| AGREEMENT : accepted
  AGREEMENT ||--o| DISBURSEMENT_SIMULATION : simulates
  APPLICATION ||--o{ JOB : queue
  APPLICATION ||--o{ AUDIT_EVENT : history
  APPLICATION ||--o{ INFO_REQUEST : clarify
```

## Миграции и seed

```bash
export DATABASE_URL=postgresql+psycopg://alfa:alfa@127.0.0.1:5432/alfa_credit
cd backend && alembic upgrade head
PYTHONPATH=.. python -m backend.app.identity.seed
```

Seed идемпотентен и **не удаляет** заявки (B08, тест `test_seed_idempotent`).  
Демо-аккаунты: [demo-accounts.md](demo-accounts.md).
