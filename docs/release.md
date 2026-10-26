# Релиз и артефакты (B10)

## Что фиксируем перед сдачей

1. **Commit hash** на `main` после зелёного CI.
2. **Git tag** вида `v0.1.0-hackathon` (или согласованный с Димой) на этот commit.
3. **Не переписывать** сданный tag (`git tag -f` / force-push tag запрещены после передачи жюри).
4. Доступ репозитория для `alfa-hack-2026` / жюри — отдельно, вне этого файла.

## Команды (когда Дима даёт добро на tag)

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
# убедиться: CI green на этом SHA
git tag -a v0.1.0-hackathon -m "Alfa Smart Credit hackathon submission"
git push origin v0.1.0-hackathon
git rev-parse HEAD
```

## Образы и digests

Зафиксировано после compose smoke **2026-10-26** (повтор с UI-сборкой), хост **macOS arm64** (Docker Desktop linux/arm64):

| Образ | Digest |
|---|---|
| `postgres:16.6` | `sha256:557fea37a744d5f4c8faab304b0a90858b53ab119735a88c131fd19dab802f36` |
| `caddy:2.8.4` | `sha256:226d1f059b75399fe19182893c7184591c07b97afc8dfcf44eeb80c9a77a530f` |
| `caddy:2.8.4-alpine` | `sha256:af32e97399febea808609119bb21544d0265c58a02836576e32a2d082c262c17` |
| `python:3.12.8-slim-bookworm` | `sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0` |
| `node:22.14.0-bookworm-slim` | `sha256:1c18d9ab3af4585870b92e4dbc5cac5a0dc77dd13df1a5905cea89fc720eb05b` |

Прописаны в `compose.yaml` / Dockerfiles. Web: multi-stage `infra/Dockerfile.web` (Node build → Caddy SPA). При смене тега — обновить таблицу и файлы. CI на `ubuntu-latest` (amd64) может тянуть тот же multi-arch manifest; при падении pull сверить digest для amd64 отдельно.

## Lock-файлы

- Backend: версии в `backend/pyproject.toml` (pinned `==`). Отдельный `uv.lock`/`poetry.lock` не обязателен, пока зависимости ставятся через `pip install -e './backend[dev]'`.
- Frontend: `frontend/package-lock.json` (F01–F10). CI job `frontend` и Compose web-сборка используют `npm ci`.

## Архив артефактов (чеклист)

- [x] `contracts/` (openapi, statuses, risk/policy)
- [x] `docs/qa/readiness-report.md` + Postman + E2E
- [x] `docker compose` image digests (таблица выше)
- [ ] Tag + SHA в README/отчёте сдачи — после push и зелёного CI
- [ ] Лог CI run URL на tagged SHA
- [x] Не включать `.env` с секретами
