# State machine заявки (B11)

Источник истины: [`contracts/statuses.json`](../contracts/statuses.json).  
Код: `backend/app/workflow/transitions.py`, enum `backend/app/schemas/enums.py`.

Терминальные: `COMPLETED`, `REJECTED`, `DECLINED_BY_CLIENT`.

## Основной путь

```mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> SUBMITTED: submit (CLIENT)
  SUBMITTED --> CHECKING: start (WORKER)
  CHECKING --> MANUAL_REVIEW: finish (WORKER)
  MANUAL_REVIEW --> OFFERED: approve_offer (OFFICER)
  OFFERED --> ACCEPTED: accept_offer (CLIENT)
  ACCEPTED --> SIGNED: simulate_sign (CLIENT)
  SIGNED --> COMPLETED: complete_simulation (WORKER)
```

## Ветки

```mermaid
stateDiagram-v2
  CHECKING --> NEEDS_INFO: require_info (WORKER)
  CHECKING --> PROCESSING_ERROR: processing_failed (WORKER)
  PROCESSING_ERROR --> SUBMITTED: retry_checks (OFFICER)
  NEEDS_INFO --> NEEDS_INFO: save_supplement (CLIENT)
  NEEDS_INFO --> SUBMITTED: resubmit (CLIENT)
  MANUAL_REVIEW --> NEEDS_INFO: request_info (OFFICER)
  MANUAL_REVIEW --> REJECTED: reject (OFFICER)
  OFFERED --> DECLINED_BY_CLIENT: decline_offer (CLIENT)
```

## Правила

- Статус меняется **только** разрешённой командой и актором; произвольный PATCH status запрещён.  
- Сбой имитации выдачи **оставляет** `SIGNED` (не `PROCESSING_ERROR`); officer — `RETRY_DISBURSEMENT`.  
- Клиентские подписи и выдача — **симуляция** (`is_simulation`).
