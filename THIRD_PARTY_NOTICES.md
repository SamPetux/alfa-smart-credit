# Сторонние компоненты — предварительный реестр

Часть D06/R10. Это инвентаризация установленной backend-среды, **не завершённый комплект лицензий и NOTICE**. Источник: Name/Version/License-Expression либо License из importlib.metadata локальной .venv. Метаданные не заменяют оригинальные тексты лицензий и юридическую проверку условий распространения. Пакеты включают runtime и dev-зависимости; список не является lock-файлом.

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

В Compose/Dockerfiles используются Python 3.12.8 slim-bookworm, PostgreSQL 16.6, Caddy 2.8.4 и Caddy 2.8.4-alpine. Базовые образы включают дополнительные системные пакеты: их лицензии и исходные NOTICE ещё не инвентаризированы. В frontend/package.json пока нет установленных React/Vite-зависимостей; планируемый стек не выдаётся за проверенный состав поставки.

Локальные симуляторы БКИ/реестра — учебная реализация проекта на синтетических fixtures, а не подключённые поставщики внешних данных. Реальные БКИ, банк и платные API не используются основным backend-сценарием.

## Перед завершением R10/Q06

Дмитрию совместно с владельцами: собрать оригинальные LICENSE/NOTICE для фактически распространяемых пакетов и бинарных включений (особенно psycopg-binary), проверить лицензии базовых образов и их пакетов, добавить будущие frontend-зависимости после появления lockfile, повторить инвентаризацию для релизной версии. Build-time зависимости, устанавливаемые изолированно setuptools, этим списком не покрыты. Лицензия самого проекта здесь не назначается.
