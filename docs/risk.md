# Кредитная логика (risk-v1 / policy-v1 / score-v1)

Фактическая реализация чистого модуля `backend/app/risk/`. Без сети, БД и FastAPI.
Worker вызывает `evaluate` только после feature builder и при `sources_complete=true`.

## Версии

| Контракт | Где | Назначение |
|---|---|---|
| `risk-v1` | `contracts/schemas/risk-v1.*.json`, `schemas/risk.py` | Вход/выход `evaluate` |
| `policy-v1` | `contracts/schemas/policy-v1.json` | Продукты, ставки, DSCR, стоп-факторы |
| `score-v1` | `backend/app/risk/score.py` | Балльная эвристика (не вероятность одобрения) |

Обновление правил меняет только новые evaluation run; прошлые результаты не пересчитываются.

## Порядок `evaluate`

1. Контрактная проверка (`sources_complete`, product config).
2. `NEEDS_INFO` при missing полях или расхождении declared/verified debt.
3. Стоп-факторы → `REJECT` (`REGISTRY_INACTIVE`, `BUSINESS_TOO_YOUNG`, `OVERDUE_LIMIT`, `CASHFLOW_NON_POSITIVE`); score может быть `null`.
4. Score и band; band `C` → `REJECT` / `RISK_POLICY_LIMIT`.
5. Доступность запрошенной суммы по DSCR; иначе поиск меньшей суммы на том же сроке (floor step 1000 ₽) с повторной проверкой DSCR.
6. Если минимума продукта нет → `AFFORDABILITY_BELOW_MINIMUM`.
7. `OFFER` с `candidate` (в т.ч. `is_alternative`) и `affordability`; `requires_officer=true`.

Статусы заявки и подтверждение OFFICER / принятие клиентом — вне этого модуля (workflow API).

## Деньги

- Все суммы — `Decimal`, в JSON — строки с двумя знаками.
- Missing не подменяется нулём.
- Платёж: аннуитет, затем ceil до копейки; график с процентами `ROUND_HALF_UP`.
- `DSCR = C / (D + A)`; `C = R − O` (O без долговых платежей).

## Модули

| Файл | Ответственность |
|---|---|
| `evaluate.py` | Оркестрация правил |
| `score.py` | Факторы AGE / MARGIN / PAYMENT_HISTORY / EXISTING_DEBT |
| `policy.py` | Загрузка versioned JSON |
| `money.py` | Платёж, DSCR, P_max |
| `features.py` | Сборка `RiskInput` из draft + симуляторов |
| `explanations.py` | reason_codes и тексты |

## Словарь признаков (S01)

| Поле | Единица | Период | Missing | Источник |
|---|---|---|---|---|
| monthly_revenue | RUB | среднемесячный | null | клиент |
| monthly_operating_costs | RUB | среднемесячный, без кредитных платежей | null | клиент |
| declared_monthly_debt_payments | RUB | среднемесячный | null | клиент |
| verified_monthly_debt_payments | RUB | среднемесячный | null | симулятор БКИ |
| company_age_months | месяц | с регистрации | null | симулятор реестра |
| registry_status | ACTIVE/INACTIVE | на observed_at | null | симулятор реестра |
| max_overdue_days_12m | день | 12 месяцев | null | симулятор БКИ |
| required_documents_present | bool | по продукту | false | документы заявки |

Технические исходы источника (`timeout` / `unavailable` / `schema_error` / incomplete) не смешиваются с фактами о компании и не передаются в `evaluate` как нули.

## Fixtures

Синтетические профили: `fixtures/profiles/`. Ожидаемые исходы golden: `fixtures/golden/`. Входные данные в fixtures; результат всегда считает `evaluate`.
