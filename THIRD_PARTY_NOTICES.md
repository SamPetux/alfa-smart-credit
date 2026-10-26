# Сторонние компоненты — предварительный реестр

Часть D06/R10. Это инвентаризация установленной backend-среды, **не завершённый комплект лицензий и NOTICE всей поставки**. Источник: Name/Version/License-Expression либо License из importlib.metadata локальной .venv. Для всех 36 сторонних Python-пакетов сохранены [44 оригинальных файла лицензий и уведомлений с SHA-256](docs/licenses/python/README.md). Метаданные и копии файлов не заменяют проверку условий распространения и состава поставки. Пакеты включают runtime и dev-зависимости; список не является lock-файлом.

Прямые runtime-зависимости: FastAPI (API), Uvicorn (ASGI), Pydantic (DTO), SQLAlchemy (ORM), Alembic (миграции), Psycopg (PostgreSQL), python-multipart (загрузка файлов). Dev: pytest, httpx и ruff. Остальные строки — установленные транзитивные зависимости. Источник объявлений — [backend/pyproject.toml](backend/pyproject.toml).

| Python-пакет | Установленная версия | Лицензия по метаданным |
|---|---|---|
| alembic | 1.20.1 | MIT |
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| click | 8.5.0 | BSD-3-Clause |
| fastapi | 0.162.0 | MIT |
| h11 | 0.16.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httptools | 0.9.0 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| Mako | 1.4.3 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| psycopg | 3.3.6 | LGPL-3.0-only |
| psycopg-binary | 3.3.6 | LGPL-3.0-only |
| pydantic | 2.14.1 | MIT |
| pydantic_core | 2.50.1 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pytest | 8.4.2 | MIT |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| python-multipart | 0.0.20 | Apache-2.0 |
| PyYAML | 6.0.3 | MIT |
| ruff | 0.17.2 | MIT |
| SQLAlchemy | 2.1.6 | MIT |
| starlette | 1.10.0 | BSD-3-Clause |
| typing-inspection | 0.4.4 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| uvicorn | 0.54.0 | BSD-3-Clause |
| uvloop | 0.23.0 | MIT License |
| watchfiles | 1.3.0 | MIT |
| websockets | 17.3 | BSD-3-Clause |

## Компоненты вне Python-реестра

В Compose/Dockerfiles используются Python 3.12.8 slim-bookworm, PostgreSQL 16.6, Caddy 2.8.4 и Caddy 2.8.4-alpine, Node 22.14 bookworm-slim (build web). Базовые образы включают системные пакеты ОС: их полный NOTICE **не** инвентаризирован (ограничение R10). Digests — [docs/release.md](docs/release.md).

## Frontend (прямые зависимости, `frontend/package.json` + lock)

| Пакет | Версия | Лицензия (типичная / npm) |
|---|---|---|
| react / react-dom | 19.1.0 | MIT |
| react-router | 7.18.4 | MIT |
| @tanstack/react-query | 5.81.5 | MIT |
| motion | 12.43.0 | MIT |
| @fontsource-variable/onest | 5.3.1 | OFL-1.1 (шрифт) |
| vite | 6.4.5 (dev) | MIT |
| typescript | 5.8.3 (dev) | Apache-2.0 |
| vitest / testing-library / jsdom | см. package.json (dev) | MIT / прочие open-source |

Полные транзитивные деревья — через `npm ls` на lockfile; копии LICENSE frontend в `docs/licenses/` не дублировались (ограничение). E2E: `@playwright/test` только в `tests/e2e` (dev QA).

Локальные симуляторы БКИ/реестра — учебная реализация на синтетических fixtures. Реальные БКИ, банк и платные API основным сценарием не используются.

## Перед формальным аудитом лицензий

Сверить psycopg-binary и base-image NOTICE; при необходимости доложить копии LICENSE frontend. Лицензия самого учебного проекта здесь не назначается.
