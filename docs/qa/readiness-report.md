# Q07 — отчёт о готовности к сдаче

Дата: 2026-10-26.  
SHA: см. tag `v0.1.0-hackathon` (`git rev-list -n 1 v0.1.0-hackathon`).  
Исполнитель QA-артефактов: репозиторий (закрытие Qxx за Рамазана по поручению владельца проекта).

## Вердикт

**Можно сдавать учебный P0.** Локально: unit 49 pass, frontend vitest 42 pass, smoke origin pass, Playwright E01+E07/E13 pass (2026-10-26, Compose :8080).  
Открытых **blocker/critical** нет. CI на tagged SHA — подтвердить после push.

## E01–E16

| ID | Результат | Доказательство |
|---|---|---|
| E01 | pass (API+E2E) | integration accept/sign; Playwright E01 ~5s на :8080 |
| E02 | pass | golden G02 / unit; UI показывает альтернативу |
| E03 | pass | `test_officer_flow.py` + UI Supplement |
| E04 | pass | golden G04; DEMO-002 → bureau `g04` |
| E05 | pass | decline в accept_sign / officer flows |
| E06 | pass | `test_worker_evaluate.py` timeout → PROCESSING_ERROR |
| E07 | pass | `test_q04_security.py` + E2E e07 |
| E08 | pass (ограничение) | volumes сохраняют данные при restart без `-v`; полный kill mid-claim — см. note |
| E09 | pass | idempotency + 409 version в integration |
| E10 | pass | B05 stale job / claim semantics в worker tests |
| E11 | pass | draft validation unit + API 422 |
| E12 | pass | локальные симуляторы; нет обязательных cloud keys |
| E13 | pass | E2E смена профиля |
| E14 | pass | 409 на устаревшей version (accept/commands) |
| E15 | pass (отчёт FE) | frontend README: 1440/768/390, без гориз. скролла |
| E16 | pass | [clean-run.md](clean-run.md) + Compose smoke |

\* E2E требует поднятый `docker compose` на `127.0.0.1:8080` и `npx playwright test` в `tests/e2e`.

## Известные ограничения (не blocker)

- Фирменные шрифты Альфы не в поставке (Onest fallback).
- Очередь банка без серверной пагинации/сортировки (limit 50).
- `company_form` — свободная строка, не enum.
- Notices образов ОС внутри Docker base images не инвентаризированы полностью.
- D07 usability-эксперимент с респондентами не проводился (гипотезы не измерены).
- Участие человека «Рамазан» заменено артефактами QA в репо по решению владельца.

## Команды повторной проверки

```bash
PYTHONPATH=. pytest backend/tests/unit -q
DATABASE_URL=… PYTHONPATH=. pytest backend/tests/integration -q
cd frontend && npm ci && npm test && npm run build
docker compose up --build -d && sh infra/scripts/smoke-origin.sh
cd tests/e2e && npm ci && npx playwright install chromium && npm test
```
