# D05 — соответствие требованиям и фактическое покрытие

Владелец: Дмитрий. Проверяющий: Рамазан (участие не подтверждено). Основа R01–R18 — [задание](planning/01-team-instructions.md). Состояние кода сверено с `origin/main` на коммите `26ce41b` (B06–B11). Полная независимая приёмка не проводилась.

Статусы: **не начато / в работе / проверено / ограничение**. «В работе» означает наличие частичной реализации или материалов, а не подтверждение участия назначенного человека. «Проверено» допустимо только для указанного объёма с доказательством; наличие теста само по себе недостаточно.

На текущем `origin/main` выполнены 36 unit-тестов без пропусков и проверка OpenAPI на 30 операций. Compose/integration-прогон в этой задаче не выполнен из-за сетевого сбоя Docker build; это локальная проверка backend, не E01–E16 и не независимая приёмка QA. Для воспроизводимой записи результатов см. [проверки backend](backend-development.md).

| ID | Owner | Статус | Реализация / артефакт | Проверка / подтверждение и оставшийся пробел |
|---|---|---|---|---|
| R01 | Дмитрий | в работе | [Исследование](research.md), [MVP](product.md) | Два сценария и явные гипотезы подготовлены; интервью и исходный PDF непосредственно не проверены |
| R02 | Игорь, Олег | в работе | API заявок и bank flow в `origin/main` | Backend покрывает решения/offer и клиентские accept/decline; UI и полный E01/E2E не выполнены |
| R03 | Илья, Игорь; Олег — API | в работе | risk/worker и bank flow в `origin/main` | Unit-проверки risk пройдены; независимое подтверждение правил, банковский UI и полный E02 отсутствуют |
| R04 | Олег | в работе | [ORM](../backend/app/db/models.py), [service](../backend/app/applications/service.py), [claim](../backend/app/jobs/claim.py) | [test_schema_migration.py](../backend/tests/integration/test_schema_migration.py), [test_applications_api.py](../backend/tests/integration/test_applications_api.py); E08/E09 для всего пути и E10 не выполнены |
| R05 | Олег | в работе | Git-репозиторий, локальная база `72ba781` | Тег сдачи, дедлайн и доступ жюри не подтверждены; локальный HEAD не равен релизу |
| R06 | Олег | в работе | [Compose](../compose.yaml), [Dockerfile](../infra/Dockerfile.api) | В облачной среде стек запускался с внешним override; чистый запуск штатного Compose на другой машине не подтверждён, Q05 открыт |
| R07 | Олег, Игорь | в работе | [Python pins](../backend/pyproject.toml), [frontend manifest](../frontend/package.json) | Версии прямых Python зависимостей закреплены; frontend lockfile, полный lock и image digests отсутствуют |
| R08 | Дмитрий; Олег — проверка | в работе | [README](../README.md), [инструкция backend](backend-development.md) | Backend-проверки описаны; посторонний пользователь ещё не прошёл полный E01 по README |
| R09 | Илья, Олег | в работе | [Seed](../backend/app/identity/seed.py), [аккаунты](demo-accounts.md), [fixtures](../fixtures/golden/cases.json) | [test_auth_api.py](../backend/tests/integration/test_auth_api.py), повтор seed при старте; независимая проверка всего набора fixtures не выполнена |
| R10 | Дмитрий, владельцы компонентов | в работе | [Предварительные notices](../THIRD_PARTY_NOTICES.md), [оригинальные лицензии Python](licenses/python/README.md) | Метаданные и 44 файла лицензий/уведомлений 36 Python-пакетов собраны; сверка поставки, frontend/образы и проверка владельцами остаются открытыми |
| R11 | Олег, Илья, Рамазан | в работе | [ADR](adr/001-modular-monolith.md), [модель данных](data-model.md), [OpenAPI](../contracts/openapi.yaml), [risk](risk.md) | [Backend tests](../backend/tests/); нет завершённых API-руководства, коллекции запросов и независимого комплекта Q06; drift OpenAPI не проверен |
| R12 | Олег | в работе | [Симуляторы](../backend/app/integrations/simulators.py), [config](../backend/app/core/config.py) | Backend работает с локальными fixtures; E12 с блокированными исходящими запросами для всего продукта не выполнялся |
| R13 | Игорь, Олег | в работе | request-info/resubmit в `origin/main` | Backend-ветка есть; UI и E03/E2E ещё не выполнены |
| R14 | Дмитрий | в работе | [Допущения](assumptions.md), [web-заглушка](../infra/proxy/web-placeholder.html) | Ограничения описаны; метки на будущих рабочих экранах проверить нельзя |
| R15 | Игорь | ограничение | [Frontend scaffold](../frontend/package.json) | Это заглушка; нет рабочего веб-кабинета, E15 не выполнялся |
| R16 | Олег | в работе | [Manifest](../backend/pyproject.toml), [risk](../backend/app/risk/evaluate.py) | В текущем backend нет обязательной LLM-зависимости; сетевой аудит E12 и проверка будущего frontend не выполнены |
| R17 | Илья | в работе | [Score](../backend/app/risk/score.py), [policy](../backend/app/risk/policy.py) | [test_risk_evaluate.py](../backend/tests/unit/test_risk_evaluate.py), [test_risk_money.py](../backend/tests/unit/test_risk_money.py); независимый пересчёт Ильёй/QA не подтверждён |
| R18 | Все владельцы, QA | в работе | [Доступ](../backend/app/identity/deps.py), [валидация](../backend/app/applications/validation.py), [план развития](planning/02-architecture.md) | [test_auth_api.py](../backend/tests/integration/test_auth_api.py), [test_transitions.py](../backend/tests/unit/test_transitions.py); полной проверки IDOR/CSRF/recovery/UX нет |

Правило обновления: добавлять commit, команду, окружение и фактический результат; различать пройденное, упавшее, пропущенное и непроведённое. На текущем `origin/main` зафиксированы 36 unit-тестов и OpenAPI на 30 операций; integration/Compose и независимая приёмка остаются непроведёнными. Не повышать статус требования на основании существования схемы или короткого smoke. Следующие блокеры и владельцы — [backlog](backlog.md).
