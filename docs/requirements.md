# D05 — соответствие требованиям и фактическое покрытие

Владелец: Дмитрий. Проверяющий: Рамазан (участие не подтверждено). Основа R01–R18 — [задание](planning/01-team-instructions.md). Состояние кода сверяется с backend-коммитом `26ce41b` в `origin/main`; наша рабочая ветка пока не синхронизирована с ним. Полная независимая приёмка не проводилась. Статусы: **не начато / в работе / проверено / ограничение**. «В работе» означает наличие частичной реализации или материалов, а не подтверждение участия назначенного человека. «Проверено» допустимо только для указанного объёма с доказательством; наличие теста само по себе недостаточно.

При настройке этой среды ранее выполнены 29 unit и 11 PostgreSQL integration тестов без пропусков, а также HTTP-путь до MANUAL_REVIEW. Это локальная проверка backend, не E01–E16 и не независимая приёмка QA. Для воспроизводимой текущей записи результатов см. [проверки backend](backend-development.md).

| ID | Owner | Статус | Реализация / артефакт | Проверка / подтверждение и оставшийся пробел |
|---|---|---|---|---|
| R01 | Дмитрий | в работе | [Исследование](research.md), [MVP](product.md) | Два сценария и явные гипотезы подготовлены; интервью и исходный PDF непосредственно не проверены |
| R02 | Игорь, Олег | в работе | API заявок; целевой E01 описан в `origin/main` | Backend добавил decision/offer/accept/sign endpoints и тесты B07; UI остаётся заглушкой, полный E01/E2E не выполнен |
| R03 | Илья, Игорь; Олег — API | в работе | risk/worker и `origin/main` bank API | `test_officer_flow.py` покрывает approve, request-info/resubmit и reject; независимое подтверждение Ильёй/QA и банковский UI отсутствуют |
| R04 | Олег | в работе | [ORM](../backend/app/db/models.py), [service](../backend/app/applications/service.py), [claim](../backend/app/jobs/claim.py) | [test_schema_migration.py](../backend/tests/integration/test_schema_migration.py), [test_applications_api.py](../backend/tests/integration/test_applications_api.py); E08/E09 для всего пути и E10 не выполнены |
| R05 | Олег | в работе | Git-репозиторий, локальная база `72ba781` | Тег сдачи, дедлайн и доступ жюри не подтверждены; локальный HEAD не равен релизу |
| R06 | Олег | в работе | Compose/Dockerfiles и `origin/main` pinned digests | README сообщает Compose smoke OK на macOS arm64; отдельный чистый прогон этой ветки и независимый Q05 остаются открытыми |
| R07 | Олег, Игорь | в работе | Python pins, Compose/Dockerfile digests | Backend pins и image digests добавлены; frontend lockfile отсутствует, полный release lock не подтверждён |
| R08 | Дмитрий; Олег — проверка | в работе | README, API guide в `origin/main`, backend-development | README/API guide обновлены в origin/main; внешний пользователь и полный E01 по README не проверены |
| R09 | Илья, Олег | в работе | [Seed](../backend/app/identity/seed.py), [аккаунты](demo-accounts.md), [fixtures](../fixtures/golden/cases.json) | [test_auth_api.py](../backend/tests/integration/test_auth_api.py), повтор seed при старте; независимая проверка всего набора fixtures не выполнена |
| R10 | Дмитрий, владельцы компонентов | в работе | [Предварительные notices](../THIRD_PARTY_NOTICES.md), [оригинальные лицензии Python](licenses/python/README.md) | Метаданные и 44 файла лицензий/уведомлений 36 Python-пакетов собраны; сверка поставки, frontend/образы и проверка владельцами остаются открытыми |
| R11 | Олег, Илья, Рамазан | в работе | ADR, as-built docs, API guide, OpenAPI snapshot | API/architecture/state docs и OpenAPI snapshot добавлены; коллекция Q06, независимая приёмка и release комплект не закрыты |
| R12 | Олег | в работе | [Симуляторы](../backend/app/integrations/simulators.py), [config](../backend/app/core/config.py) | Backend работает с локальными fixtures; E12 с блокированными исходящими запросами для всего продукта не выполнялся |
| R13 | Игорь, Олег | в работе | bank request-info, client resubmit в `origin/main` | `test_officer_flow.py` проверяет NEEDS_INFO и resubmit; UI и E03/E2E ещё не выполнены |
| R14 | Дмитрий | в работе | [Допущения](assumptions.md), [web-заглушка](../infra/proxy/web-placeholder.html) | Ограничения описаны; метки на будущих рабочих экранах проверить нельзя |
| R15 | Игорь | ограничение | [Frontend scaffold](../frontend/package.json) | Это заглушка; нет рабочего веб-кабинета, E15 не выполнялся |
| R16 | Олег | в работе | [Manifest](../backend/pyproject.toml), [risk](../backend/app/risk/evaluate.py) | В текущем backend нет обязательной LLM-зависимости; сетевой аудит E12 и проверка будущего frontend не выполнены |
| R17 | Илья | в работе | [Score](../backend/app/risk/score.py), [policy](../backend/app/risk/policy.py) | [test_risk_evaluate.py](../backend/tests/unit/test_risk_evaluate.py), [test_risk_money.py](../backend/tests/unit/test_risk_money.py); независимый пересчёт Ильёй/QA не подтверждён |
| R18 | Все владельцы, QA | в работе | Доступ, validation, logging/reliability docs/tests | Добавлены request-id/privacy/demo-off/reclaim проверки; полной IDOR/CSRF/recovery/UX приёмки нет |

Правило обновления: добавлять commit, команду, окружение и фактический результат; различать пройденное, упавшее, пропущенное и непроведённое. Не повышать статус требования на основании существования схемы или успешного короткого smoke. Следующие блокеры и владельцы — [backlog](backlog.md). Новые backend-тесты обнаружены в `origin/main`, но в текущей рабочей ветке не запускались.
