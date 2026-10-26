# Архитектура as-built (B11)

Проектный канон: [planning/02-architecture.md](planning/02-architecture.md) и [ADR 001](adr/001-modular-monolith.md).  
Этот файл описывает **то, что реализовано** в репозитории на момент B01–B10, без заявлений production-ready и банковского соответствия.

## Форма

Модульный монолит: один backend-образ для **API** и **worker**, PostgreSQL, reverse proxy (Caddy), web — production-сборка frontend (`infra/Dockerfile.web`).

```text
browser → proxy:8080
            ├─ /api/*  → api:8000
            └─ /*      → web:80 (SPA frontend/dist)
worker ←→ PostgreSQL ←→ api
         documents volume (не static)
```

Compose: `db` → `init` (migrate + idempotent seed) → `api` + `worker` → `web` → `proxy` (`127.0.0.1:8080`). БД наружу не публикуется.

## Модули backend

| Пакет | Назначение |
|---|---|
| `identity/` | Сессии cookie, CSRF, demo/login, seed |
| `applications/` | Черновик, submit, officer, accept/sign |
| `workflow/` | Таблица переходов (зеркало `contracts/statuses.json`) |
| `jobs/` | Claim/lease, evaluate pipeline, disbursement |
| `integrations/` | Локальные симуляторы БКИ/реестра + fixtures |
| `risk/` | Чистый score/policy (Илья); без ORM/сети |
| `documents/` | Volume storage, MIME/сигнатуры |
| `api/v1/` | HTTP; контракт `contracts/openapi.yaml` |

## Потоки P0 (реализованы на API)

1. Клиент: DRAFT → submit → worker CHECKING → MANUAL_REVIEW  
2. Officer: request-info / approve / reject; клиент resubmit  
3. Клиент: accept/decline → agreement → simulate-sign → worker COMPLETED  
4. Officer: retry-checks (PROCESSING_ERROR), retry-disbursement (SIGNED + failed job)

Идемпотентность: `Idempotency-Key` + `expected_version`. Money = Decimal / JSON string.

## Наблюдаемость и demo (B09)

- `GET /api/v1/health/live`, `…/ready` (503 если БД/миграции недоступны)  
- Structured JSON logs: `event_code`, `request_id`, `application_id` — без токенов и тел документов  
- `DEMO_MODE=false` отключает `/demo/*`; `APP_ENV=production` отвергает demo-defaults  

## Что ещё не as-built

- Полный UI кабинетов (Игорь), frontend lock  
- Digests образов `@sha256` (см. [release.md](release.md))  
- Независимый E2E/E01 с UI (Рамазан)  
- Вторая CPU-архитектура: см. [platforms](#платформы)

## Платформы

- **macOS arm64**: unit/integration + **Compose smoke OK** (2026-10-26), digests в compose/Dockerfiles.  
- **linux/amd64**: целевой CI (`ubuntu-latest`); compose-smoke в GitHub Actions.  
Не утверждать полную multi-arch матрицу без отчёта Q05 на чистом clone.
