# ADR 001: Модульный монолит с отдельным worker

- Status: Accepted (G0 каркас)
- Date: 2026-10-24
- Owner: Олег

## Context

Нужен автономный прототип кредитного кабинета (клиент + сотрудник) с durable обработкой проверок, без микросервисной сложности и без отдельного сетевого сервиса скоринга.

Репозиторий был пустым (только README). Стек выбран по `docs/planning/02-architecture.md`.

## Decision

- Один backend-пакет (FastAPI + SQLAlchemy + Alembic + PostgreSQL).
- Worker — отдельный процесс на том же образе, читает jobs из PostgreSQL.
- Risk — чистая библиотека внутри `backend/app/risk/` (владелец Илья), без ORM/сети.
- Frontend — одно React/TypeScript приложение (два кабинета), один origin через reverse proxy.
- Канонические контракты в `contracts/` (OpenAPI, statuses, risk-v1, policy-v1).

## Consequences

- Плюсы: общие типы, атомарные транзакции status+job+audit, проще демо и CI.
- Минусы: модули пока не масштабируются независимо; очередь на PostgreSQL не замена брокеру при высокой нагрузке.
- Версии Python-зависимостей зафиксированы в `backend/pyproject.toml` (локальная сборка 2026-10-25).
- Образы Compose: `python:3.12.8-slim-bookworm`, `postgres:16.6`, `caddy:2.8.4` (не `latest`). Digests — после успешного CI/Compose на рабочей машине (B10); Docker daemon на машине разработки на момент B01 мог быть недоступен.

## Alternatives considered

- Микросервисы на каждый модуль — отвергнуто для P0 (интеграционный риск и срок).
- Отдельный HTTP risk-service — отвергнуто (лишняя сеть, дублирование контрактов).
- SQLite вместо PostgreSQL — отвергнуто для интеграционных/релизных проверок.
