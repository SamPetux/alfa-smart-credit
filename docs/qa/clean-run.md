# Q05 — чистый запуск (факт)

Дата: 2026-10-26. Исполнитель: QA в репозитории (за Рамазана). Хост: macOS 26.5.2, CPU **arm64**, RAM ≈16+ GB (hw.memsize).  
Docker 29.8.0, Compose v5.5.1. Сеть нужна **только** для первичной загрузки образов/npm в build; runtime после `compose up` — локальный (симуляторы, без cloud keys).

## Команды

```bash
git clone <repo> && cd alfa-smart-credit
docker compose down -v   # чистое окружение
time docker compose up --build -d
# дождаться healthy api
sh infra/scripts/smoke-origin.sh
# UI: http://127.0.0.1:8080/demo
```

## Замеры (этот хост)

| Этап | Результат |
|---|---|
| Первый `compose up --build` после redesign (оценка) | ~1–2 мин при тёплом cache Node/pip; холодный build web дольше |
| Повторный старт (`compose up -d` без rebuild) | секунды до healthy |
| Smoke | pass: live, ready, SPA index + `/demo` |
| Повторный seed (`init`) | идемпотентен; пользовательские заявки в volume `pgdata` сохраняются при `down` без `-v` |

Разрушительный сброс: только `docker compose down -v` (удаляет volumes) — документирован в README/backend-development.

## Автономность

После сборки образов основной сценарий E01 не требует внешних HTTP API банка/БКИ/LLM.  
Непроверено в этом отчёте: чистый clone на linux/amd64 без кэша (ожидается CI `compose-smoke`).
