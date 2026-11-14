# Corporate Event Management API

A REST API for Acme Corp's internal event system. Employees create an account, log in
with a JWT, publish corporate events (title, description, date, location, capacity) and
register for them. The API stops duplicate sign-ups, refuses sign-ups when an event is
full and returns clear JSON errors for every broken rule.

Built with **FastAPI**, **PostgreSQL (Neon)**, **SQLAlchemy 2.0 async** and **Pydantic v2**.
A small React frontend in [`frontend/`](frontend/README.md) uses the same API.

**Bonus features included:** pagination (`skip`/`limit`), title and date filters,
JWT authentication, an async database layer end to end, and a pytest suite.

## Contents

- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup with uv](#setup-with-uv)
- [Neon PostgreSQL setup](#neon-postgresql-setup)
- [Configure `.env`](#configure-env)
- [Run the API](#run-the-api)
- [Run the frontend (optional)](#run-the-frontend-optional)
- [Run the tests](#run-the-tests)
- [API endpoints](#api-endpoints)
- [Screenshots](#screenshots)
- [Git workflow](#git-workflow)
- [AI usage](#ai-usage)

## Tech stack

| Concern | Choice | Why |
| --- | --- | --- |
| Language and packaging | Python 3.12 managed by `uv` | One tool for the virtual environment, dependencies and running commands |
| Web framework | `fastapi[standard]` | Async, automatic Swagger docs; includes Uvicorn, `fastapi dev` and form parsing for login |
| Database | Neon serverless PostgreSQL | Nothing to install locally; a separate Neon branch gives the tests their own database |
| ORM and driver | SQLAlchemy 2.0 async + `asyncpg` | `AsyncSession` everywhere, no blocking database calls |
| Migrations | Alembic (async template) | Versioned schema changes |
| Settings | `pydantic-settings` | Reads secrets from `.env`, so nothing is hard-coded |
| Auth | `PyJWT` + `pwdlib[argon2]` | Signed HS256 tokens and argon2 password hashing |
| Tests | `pytest`, `pytest-asyncio`, `httpx` | Async HTTP tests against a real PostgreSQL test database |
| Lint and format | `ruff` | PEP 8 checks and formatting in one command |
| Frontend | React + Vite + TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query | Demo client; see [`frontend/README.md`](frontend/README.md) |

## Project structure

```text
event-management-app/
├── app/
│   ├── main.py                  # create_app(): CORS, routers, exception handler, /health
│   ├── db.py                    # async engine, session factory, Base, get_db()
│   ├── core/
│   │   ├── config.py            # Settings loaded from .env
│   │   ├── security.py          # argon2 password hashing, JWT encode/decode
│   │   └── exceptions.py        # domain exceptions (EventNotFoundError, EventFullError, ...)
│   ├── models/                  # SQLAlchemy ORM models, one module per table
│   │   ├── user.py
│   │   ├── event.py
│   │   └── registration.py
│   ├── schemas/                 # Pydantic request and response models
│   │   ├── common.py            # ErrorResponse, pagination parameters
│   │   ├── user.py
│   │   ├── event.py
│   │   └── registration.py
│   ├── services/                # all business rules; no FastAPI imports
│   │   ├── auth_service.py
│   │   ├── event_service.py
│   │   └── registration_service.py
│   └── api/
│       ├── deps.py              # SessionDep and CurrentUser dependencies
│       ├── responses.py         # shared OpenAPI error-response documentation
│       └── routes/              # thin routers: auth.py, events.py, registrations.py
├── alembic/  alembic.ini        # database migrations
├── tests/                       # pytest suite (see "Run the tests")
├── frontend/                    # React + Vite client
├── docs/                        # screenshots/, ai-logs/, AI_USAGE.md, DEVELOPMENT_PLAN.md
├── .env.example                 # template for your .env
├── pyproject.toml / uv.lock     # dependencies (uv)
└── requirements.txt             # the same dependencies for pip
```

### Where the five required files live

The brief names five files. Each one is kept as a module or package with the same name:

| File in the brief | Location in this project | Holds |
| --- | --- | --- |
| `db.py` | [`app/db.py`](app/db.py) | Async engine, session factory, `Base`, `get_db()` |
| `models.py` | [`app/models/`](app/models) | One ORM model per table: `User`, `Event`, `Registration` |
| `schemas.py` | [`app/schemas/`](app/schemas) | Create / Update / Read schemas with validation |
| `services.py` | [`app/services/`](app/services) | Business rules, one service per resource |
| `main.py` | [`app/main.py`](app/main.py) + [`app/api/routes/`](app/api/routes) | App factory, plus one thin router per resource |

### How a request flows

```text
Client -> api/routes/ -> services/ -> models/ + db.py -> PostgreSQL (Neon)
             ^ schemas/ validate input and shape output
             services raise domain exceptions -> one handler in main.py -> 401 / 403 / 404 / 409
```

Routes only parse the request, call one service function and return its result.
Services hold every rule (duplicate sign-up, full event, missing event, ownership) and
raise exceptions from `app/core/exceptions.py`; one handler in `app/main.py` turns them
into JSON errors with the same shape: `{"detail": "<message>"}`.

## Prerequisites

- **Python 3.12** and **[uv](https://docs.astral.sh/uv/getting-started/installation/)**
  (`uv` can install Python for you)
- **Git**
- A free **[Neon](https://neon.tech)** account (hosted PostgreSQL)
- **Node.js LTS** and npm, only if you want to run the frontend

## Setup with uv

```powershell
git clone https://github.com/abidroid/event-management-app.git
cd event-management-app
uv sync            # creates .venv and installs app + dev dependencies from uv.lock
```

Using pip instead of uv:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(Then drop the `uv run` prefix from the commands below.)

## Neon PostgreSQL setup

The app uses two separate databases, one for development and one for tests, so tests
never touch your development data. On Neon these are two **branches** of one project.

1. Sign in to the [Neon console](https://console.neon.tech) and create a project,
   for example `event-management-app`, in the region closest to you.
2. Keep the default branch, **`production`**. This is the **development** database.
3. Open **Branches -> Create branch**, name it **`test`**, and create it from `production`.
   This is the **test** database used by pytest.
4. For each branch, click **Connect**, turn **Connection pooling off** and copy the
   **direct** connection string (the hostname must *not* contain `-pooler`).
   The pooled endpoint runs PgBouncer, which clashes with asyncpg's prepared statements.

Paste the strings exactly as Neon shows them, ending in
`?sslmode=require&channel_binding=require`. asyncpg does not accept those parameters,
so `app/db.py` converts the URL to `postgresql+asyncpg://`, removes them and enables SSL
through `connect_args={"ssl": "require"}` instead. It also sets `pool_pre_ping=True` and
`pool_recycle=300`, because Neon suspends idle databases and closes their connections.

## Configure `.env`

```powershell
copy .env.example .env
```

Then edit `.env` (it is git-ignored; never commit it):

| Variable | Required | Value |
| --- | --- | --- |
| `DATABASE_URL` | yes | Direct connection string of the Neon `production` branch |
| `TEST_DATABASE_URL` | yes | Direct connection string of the Neon `test` branch |
| `JWT_SECRET_KEY` | yes | A long random string; generate one with `uv run python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | no | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Default `30` |
| `CORS_ORIGINS` | no | JSON list of browser origins, default `["http://localhost:5173"]` (the frontend) |

## Run the API

```powershell
uv run alembic upgrade head        # create the tables on the development database
uv run fastapi dev app/main.py     # start the server with auto-reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health check: <http://127.0.0.1:8000/health>

To try protected endpoints in Swagger: call `POST /auth/register`, then click
**Authorize**, enter the same email (as *username*) and password, and Swagger sends the
token with every request.

After changing a model, create and apply a migration:

```powershell
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Run the frontend (optional)

With the API running, in a second terminal:

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Details, including the optional `VITE_API_URL` setting, are in
[`frontend/README.md`](frontend/README.md).

## Run the tests

```powershell
uv run pytest -v
```

The tests run against the Neon **`test`** branch (`TEST_DATABASE_URL`), never the
development database and never SQLite, so `ILIKE`, row locks and constraints behave
exactly as in production. Tables are created once per test session and truncated before
every test, so each test starts from an empty database. Each request goes over the
network to Neon, so the full suite takes several minutes.

Result of the last full run:

```text
====================== 112 passed in 2335.81s (0:38:55) =======================
```

| Test file | Covers |
| --- | --- |
| `tests/test_auth.py` | Register, login, `/auth/me`; duplicate email 409, wrong password 401, bad or expired token 401 |
| `tests/test_events.py` | Create, list, get, update, delete; 401 without a token, 404 unknown id, 409 capacity below sign-ups |
| `tests/test_validation.py` | 422 for empty title, capacity 0, past date, missing fields; title stripping and boundary values |
| `tests/test_pagination_filtering.py` | `skip`/`limit` defaults and bounds, title and date filters, combinations |
| `tests/test_registrations.py` | Register, list, cancel, seat freed after cancel; 404, duplicate 409, full 409, 401, 403 not owner |
| `tests/test_exceptions.py` | Domain exceptions map to the right status codes and error body |
| `tests/test_docs.py` | OpenAPI schema has app metadata, tags, summaries, descriptions and documented error responses |
| `tests/test_cors.py` | The frontend origin is allowed, other origins are not |

Code-quality checks:

```powershell
uv run ruff check .            # lint (PEP 8, import order)
uv run ruff format --check .   # formatting
uv run --with mypy mypy app    # type check
```

## API endpoints

| Method | Path | Auth | Success | Errors |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | public | 201 | 409 email taken, 422 |
| POST | `/auth/login` | public (OAuth2 form) | 200 + token | 401 bad credentials |
| GET | `/auth/me` | token | 200 | 401 |
| POST | `/events` | token | 201 | 401, 422 |
| GET | `/events?skip&limit&title&date` | public | 200 | 422 |
| GET | `/events/{id}` | public | 200 | 404 |
| PUT | `/events/{id}` | token | 200 | 401, 404, 409 capacity below sign-ups, 422 |
| DELETE | `/events/{id}` | token | 204 | 401, 404 |
| POST | `/events/{id}/registrations` | token | 201 | 401, 404, 409 duplicate, 409 full, 422 |
| GET | `/events/{id}/registrations?skip&limit` | token | 200 | 401, 404 |
| DELETE | `/registrations/{id}` | token (own registration only) | 204 | 401, 403 not owner, 404 |
| GET | `/health` | public | 200 | — |

- **Pagination:** `skip` ≥ 0 (default 0) and `limit` 1–100 (default 10) on both list
  endpoints. Events are ordered by `event_date`, then `id`, so pages are stable.
- **Filters:** `title` is a case-insensitive partial match (`ILIKE '%value%'`); `date`
  matches `event_date` exactly (`YYYY-MM-DD`). Both combine with each other and with paging.
- **Registration:** there is no request body; the registrant is always the logged-in user.
  The service locks the event row (`SELECT ... FOR UPDATE`) before checking that the event
  exists (404), the user is not already registered (409) and seats are left (409), so two
  simultaneous sign-ups cannot overfill an event.
- **Errors:** every error has the body `{"detail": "<human-readable message>"}`;
  401 responses also send `WWW-Authenticate: Bearer`. Validation errors (422) use
  FastAPI's standard format listing each invalid field.

## Screenshots

Swagger screenshots, one per endpoint, showing the request and the response, are in
[`docs/screenshots/`](docs/screenshots).

| # | Endpoint | Screenshot |
| --- | --- | --- |
| 01 | `POST /auth/register` | ![](docs/screenshots/01-post-auth-register-201.png) |
| 02 | `POST /auth/login` | ![](docs/screenshots/02-post-auth-login-200.png) |
| 03 | `GET /auth/me` | ![](docs/screenshots/03-get-auth-me-200.png) |
| 04 | `POST /events` | ![](docs/screenshots/04-post-events-201.png) |
| 05 | `GET /events` | ![](docs/screenshots/05-get-events-200.png) |
| 06 | `GET /events/{id}` | ![](docs/screenshots/06-get-event-200.png) |
| 07 | `PUT /events/{id}` | ![](docs/screenshots/07-put-event-200.png) |
| 08 | `DELETE /events/{id}` | ![](docs/screenshots/08-delete-event-204.png) |
| 09 | `POST /events/{id}/registrations` | ![](docs/screenshots/09-post-registration-201.png) |
| 10 | `GET /events/{id}/registrations` | ![](docs/screenshots/10-get-registrations-200.png) |
| 11 | `DELETE /registrations/{id}` | ![](docs/screenshots/11-delete-registration-204.png) |
| 12 | `GET /health` | ![](docs/screenshots/12-get-health-200.png) |

## Git workflow

Every feature was built on its own branch and merged into `main` through a GitHub pull
request with a merge commit, so each branch stays visible in the network graph.
Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat(events): ...`, `test(...)`, `docs(...)`).

| PR | Branch | Delivers |
| --- | --- | --- |
| #1 | `feature/project-setup` | Settings, async `db.py`, Alembic, `/health` |
| #2 | `feature/event-crud` | Event model, schemas, services, five CRUD routes, test fixtures |
| #3 | `feature/validation-error-handling` | Field constraints, domain exceptions, one error handler |
| #4 | `feature/jwt-auth` | Users, register/login/me, protected event writes |
| #5 | `feature/pagination-filtering` | `skip`/`limit`, `title` and `date` filters |
| #6 | `feature/registrations` | Registrations with the duplicate, capacity and ownership rules |
| #7 | `feature/api-docs` | Tags, summaries, examples and error responses in Swagger |
| #8 | `feature/frontend` | React + Vite client |
| #9 | `docs/submission` | This README, `requirements.txt`, AI usage documentation |

## AI usage

This project was built with Claude Code. The tools, model, settings, prompts and the full
exported chat history of every phase are documented in [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
