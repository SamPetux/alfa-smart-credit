# Демо и тестовые аккаунты (B03)

Все данные синтетические. Open demo session ≠ production authentication.

## DEMO_MODE=true

`GET /api/v1/demo/profiles` → `POST /api/v1/demo/session` с `profile_id`:

| profile_id | Роль | Компания |
|---|---|---|
| `client-romashka` | CLIENT | DEMO-001 ООО «Ромашка» |
| `client-ivanov` | CLIENT | DEMO-002 ИП Иванов |
| `officer` | OFFICER | нет |

Роль всегда из БД, не из тела запроса.

## DEMO_MODE=false

Эндпоинты `/demo/*` недоступны (404). Вход: `POST /api/v1/auth/login`.

| username | password | Роль |
|---|---|---|
| `client_romashka` | `client-demo-pass` | CLIENT |
| `client_ivanov` | `client-demo-pass` | CLIENT |
| `officer` | `officer-demo-pass` | OFFICER |

Пароли хранятся как PBKDF2-SHA256. Self-service регистрации нет.

## Cookies

- `asc_session` — HttpOnly, SameSite=Lax
- `asc_csrf` — readable (double-submit); для мутаций также заголовок `X-CSRF-Token`
