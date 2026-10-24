# Контракты G0

Единый источник истины для статусов, API и risk/policy. Изменения — через Олега и затронутых владельцев (Игорь / Илья).

| Файл | Назначение |
|---|---|
| `statuses.json` | Enum статусов, terminal, команды state machine, клиентские подписи |
| `openapi.yaml` | API v1 (префикс `/api/v1`) |
| `schemas/risk-v1.input.json` | Вход `evaluate` |
| `schemas/risk-v1.output.json` | Выход `RiskResult` |
| `schemas/policy-v1.json` | Демонстрационная политика продуктов |
| `examples/` | Согласованные примеры для frontend и golden cases |

После первой генерации из FastAPI добавить snapshot `openapi.json` и сверять в CI.

Правила:

- Money в JSON — строка `"1234.56"`, не float.
- Missing ≠ 0; score/band/factors могут быть `null`.
- Техническая ошибка источника ≠ кредитный отказ.
- Клиентская и банковская проекции заявок разделены.
