# Q01 — матрица приёмки R01–R18 ↔ E01–E16

Владелец исполнения: QA (исполнено в репозитории 2026-10-26). Источник сценариев — [01-team-instructions.md](../planning/01-team-instructions.md).  
Код на момент отчёта: `main` после frontend-редизайна и backend B01–B11.

## Виды проверок

| Вид | Где | Назначение |
|---|---|---|
| smoke | `infra/scripts/smoke-origin.sh`, CI `compose-smoke` | Один origin: health + SPA |
| unit | `backend/tests/unit`, `frontend` vitest | Risk/golden, CSRF, UI-компоненты |
| API/integration | `backend/tests/integration` + PostgreSQL | Submit, officer, accept/sign, Q04 |
| E2E | `tests/e2e` (Playwright, два browser context) | Клиент + сотрудник на реальном origin |
| security | `test_q04_security.py`, E07/E13 | IDOR, CSRF, роли, demo off |
| recovery | integration worker + E08 вручную/отчёт | Lease/retry, volumes |
| clean run | [clean-run.md](clean-run.md) (Q05) | Compose с нуля на arm64 |

## Связь требований и сценариев

| R | Смысл | E-сценарии | Артефакты проверки |
|---|---|---|---|
| R01 | Исследование / JTBD | — (продукт) | `docs/research.md`, `docs/product.md` |
| R02 | Сквозной путь клиента | E01, E05, E13 | E2E `e01`, integration accept/sign |
| R03 | Банк + risk | E02, E04 | unit golden G02/G04; DEMO-002→g04; bank UI |
| R04 | Сохранение / статусы | E08, E09 | integration idempotency; Compose volumes |
| R05 | Репозиторий / сдача | E16 | git tag `v0.1.0-hackathon`, README |
| R06 | Compose | E12, E16 | compose smoke, digests в `docs/release.md` |
| R07 | Версии / locks | — | `pyproject.toml`, `package-lock.json`, digests |
| R08 | README воспроизводим | E16 | README + clean-run |
| R09 | Seed / fixtures | E16 | `test_seed_idempotent.py`, fixtures |
| R10 | Notices | Q06 | `THIRD_PARTY_NOTICES.md` + licenses |
| R11 | Контракты / доки | — | `contracts/`, `docs/api.md`, OpenAPI check |
| R12 | Без внешних API | E12 | локальные симуляторы, CI без cloud keys |
| R13 | Уточнения в продукте | E03 | officer request-info + client resubmit + UI |
| R14 | Демо-метки / ограничения | — | demo banner, assumptions |
| R15 | Веб-кабинеты | E01, E15 | frontend F01–F10, ширины в отчёте Игоря |
| R16 | Без обязательного LLM | — | explain template-v1 |
| R17 | Score/policy учебные | E02, E04 | golden G01–G05, `test_golden_cases_matrix.py` |
| R18 | Права / валидация | E07, E11, E14 | Q04 security tests |

## E01–E16 — способ проверки

| E | Способ | Статус в [readiness-report.md](readiness-report.md) |
|---|---|---|
| E01 | E2E + integration accept/sign | см. отчёт |
| E02 | unit G02 + UI offer alternative | см. отчёт |
| E03 | integration officer_flow + UI | см. отчёт |
| E04 | DEMO-002 bureau g04 + unit G04 | см. отчёт |
| E05 | integration decline + E2E опционально | см. отчёт |
| E06 | integration worker timeout | см. отчёт |
| E07 | `test_q04_security.py` | см. отчёт |
| E08 | Compose volumes + restart (Q05 notes) | см. отчёт |
| E09 | integration idempotency / 409 | см. отчёт |
| E10 | worker stale (B05 claim) — unit/integration | см. отчёт |
| E11 | draft validation unit + API 422 | см. отчёт |
| E12 | offline runtime после pull образов | см. отчёт |
| E13 | E2E смена профиля | см. отчёт |
| E14 | version conflict 409 на accept | см. отчёт |
| E15 | отчёт frontend (1440/768/390) | см. отчёт |
| E16 | clean-run.md | см. отчёт |
