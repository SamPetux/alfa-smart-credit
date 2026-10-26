# API v1 — руководство (B11)

Канон: [`contracts/openapi.yaml`](../contracts/openapi.yaml), snapshot [`contracts/openapi.json`](../contracts/openapi.json).  
Живые docs (при запущенном API): `/api/docs`, `/api/openapi.json`.  
Сверка CI: `python scripts/check_openapi_contract.py`.

Префикс: `/api/v1`. Один origin с UI через proxy (`127.0.0.1:8080`).

## Аутентификация

| Режим | Как |
|---|---|
| `DEMO_MODE=true` | `GET /demo/profiles`, `POST /demo/session` → HttpOnly cookie + CSRF |
| `DEMO_MODE=false` | `POST /auth/login` с тестовым username/password из [demo-accounts.md](demo-accounts.md) |

- Cookie сессии: `asc_session` (имя из env).  
- Изменяющие запросы: **обязателен** заголовок `X-CSRF-Token` (значение из ответа session; cookie alone недостаточно).  
- `GET /auth/me`, `POST /auth/logout`.  
- Роль и компания проверяются на сервере; UI не является ACL.

## Общие правила команд

- `expected_version` — optimistic concurrency; при рассинхроне **409** `VERSION_CONFLICT`.  
- `Idempotency-Key` обязателен на create/submit/resubmit/decision/accept/sign/retry (см. OpenAPI).  
- Money в JSON — **строка**; missing ≠ 0.  
- Ошибки: envelope `{ error: { code, message, field_errors, request_id } }`.  
- Ответ и логи несут `X-Request-Id` / `request_id`.

## Клиент

| Метод | Путь | Назначение |
|---|---|---|
| GET/POST | `/applications` | Список / создать черновик |
| GET/PATCH | `/applications/{id}` | Читать / править draft |
| GET | `/applications/{id}/documents` | Список загруженных (последний по kind) |
| POST | `/applications/{id}/documents` | Загрузка |
| GET | `/applications/{id}/documents/{doc_id}` | Скачать (attachment) |
| POST | `/applications/{id}/submit` | Отправка → 202 |
| GET | `/applications/{id}/history` | Безопасный audit |
| GET | `/applications/{id}/info-request` | Открытое уточнение |
| POST | `/applications/{id}/resubmit` | Новая ревизия |
| GET/POST | `/applications/{id}/offer…` | Offer, accept, decline |
| GET/POST | `/applications/{id}/agreement…` | Документ + simulate-sign |
| GET | `/applications/{id}/explain` | Шаблонное объяснение (`topic=general\|why\|next\|amount`), без LLM |

## Банк (OFFICER)

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/bank/applications` | Очередь |
| GET | `/bank/applications/{id}` | Досье |
| POST | `…/request-info` | NEEDS_INFO |
| POST | `…/decision` | APPROVE_OFFER / REJECT |
| POST | `…/retry-checks` | Из PROCESSING_ERROR |
| POST | `…/retry-disbursement` | SIGNED + failed job |

## Инфра

| Метод | Путь |
|---|---|
| GET | `/health/live`, `/health/ready` |
| GET | `/meta` (demo_mode, privacy_notice) |
| GET | `/products` |

Коллекция Postman/Insomnia с CSRF-flow — задача QA (Q06); в репозитории пока нет готовой коллекции.
