# Q02 — независимые ожидания и формат бага

## Ожидания пользователя (продукт, согласовано с каноном D03)

| Сценарий | Ожидание (не из кода UI) |
|---|---|
| E01 | Клиент проходит путь до статуса COMPLETED; на экране явно «выдача смоделирована»; история на сервере |
| E02 | При меньшей сумме клиент видит альтернативу и причину; score не «вероятность одобрения» |
| E03 | Список запрошенных полей; после resubmit новая revision и новый расчёт |
| E04 | Рекомендация REJECT с OVERDUE_LIMIT; сотрудник фиксирует отказ; клиент видит отказную ветку |
| E05 | DECLINED_BY_CLIENT; нет agreement/sign/disbursement |
| E06 | PROCESSING_ERROR без кредитного отказа и без фиктивного score |
| E07 | Чужие объекты → 404/403; bank API недоступен CLIENT |
| E09 | Повтор Idempotency-Key → тот же результат; устаревший expected_version → 409 |
| E11 | 422 с field_errors; статус черновика не ломается |
| E13 | После смены профиля данные прошлой компании не видны |

## Golden cases (risk)

Источник expected: [`fixtures/golden/cases.json`](../../fixtures/golden/cases.json) (владелец risk — Илья; принято как согласованное).  
Проверка: `backend/tests/unit/test_golden_cases_matrix.py` и `test_risk_evaluate.py`.  
Запрещено: генерировать expected повторным вызовом evaluate «в эталон».

Ручной пересчёт платежа G02 (независимый от risk-кода UI): аннуитет 641000 @ 22% на 12 мес → 59994.00 (см. `docs/risk.md` / money helpers в тестах).

## Формат бага

```text
Severity: blocker | critical | major | minor | note
Title:
Profile / role:
Steps:
1.
Expected:
Actual:
request_id (если есть):
Application id / revision / version:
Evidence (без секретов): HTTP status, error.code, скрин/лог
```

Blocker/critical — по определению Q07 в инструкции Рамазана.
