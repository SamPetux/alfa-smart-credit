# D05 — соответствие требованиям и фактическое покрытие

Владелец: Дмитрий. Проверяющий: QA (исполнено в репозитории 2026-10-26; роль Рамазана закрыта артефактами `docs/qa/`).  
Основа R01–R18 — [задание](planning/01-team-instructions.md). Состояние кода: `origin/main` после B01–B11, F01–F10 и редизайна.  
Независимая приёмка E01–E16: см. [qa/readiness-report.md](qa/readiness-report.md) и [qa/acceptance-matrix.md](qa/acceptance-matrix.md).

Статусы: **не начато / в работе / проверено / ограничение**. «Проверено» — есть артефакт проверки в этом релизе; не означает банковский production-аудит.

| ID | Owner | Статус | Реализация / артефакт | Проверка / пробел |
|---|---|---|---|---|
| R01 | Дмитрий | проверено | [research.md](research.md), [product.md](product.md) | Кабинетный разбор и гипотезы; живые интервью не проводились (ограничение D01) |
| R02 | Игорь, Олег | проверено | API + UI клиентский путь | E01: integration accept/sign + E2E; полный отчёт QA |
| R03 | Илья, Игорь; Олег | проверено | risk/worker + bank UI | Golden G02/G04; DEMO-002→g04; bank approve/reject |
| R04 | Олег | проверено | ORM, service, jobs | Integration idempotency/409; volumes Compose |
| R05 | Олег | в работе | Git `main` | Tag сдачи `v0.1.0-hackathon` готовится; доступ жюри — орг. |
| R06 | Олег | проверено | Compose + digests | Smoke SPA+API на arm64; CI compose-smoke |
| R07 | Олег, Игорь | проверено | pins + lockfiles + digests | `pyproject.toml`, `package-lock.json`, `docs/release.md` |
| R08 | Дмитрий; Олег | проверено | README, backend-development | Q05 clean-run зафиксирован |
| R09 | Илья, Олег | проверено | seed, demo-accounts, fixtures | seed idempotent tests; golden cases |
| R10 | Дмитрий + владельцы | в работе | notices + licenses | Python собран; frontend Onest/motion добавлены; образы — ограничение |
| R11 | Олег, Илья, QA | проверено | ADR, data-model, OpenAPI, api.md | OpenAPI drift check CI; коллекция Postman Q06 |
| R12 | Олег | проверено | симуляторы | Локальные fixtures; E12 без cloud keys |
| R13 | Игорь, Олег | проверено | request-info/resubmit + UI | Integration + UI SupplementPanel |
| R14 | Дмитрий | проверено | assumptions, demo banner | Метки демо в UI |
| R15 | Игорь | проверено | frontend кабинеты | F01–F10, редизайн; E15 — отчёт frontend |
| R16 | Олег | проверено | без обязательного LLM | explain template-v1 |
| R17 | Илья | проверено | score/policy | Golden matrix + unit; согласовано с владельцем risk |
| R18 | Все / QA | проверено | auth, CSRF header, validation | `test_q04_security.py`; E07 |

Правило: различать пройденное / упавшее / пропущенное / непроведённое. Детали pass/fail — [readiness-report.md](qa/readiness-report.md).
