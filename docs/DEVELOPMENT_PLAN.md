# Corporate Event Management API — Development Plan

Nov 11, 2026 · @Muhammad Abid

## Goal and scoring strategy

We build every mandatory feature and all five bonuses, because bonus marks (20) can recover any mandatory marks lost, up to the 100 cap. Roughly 37 of the 120 marks are earned by process and presentation, not code: Git (M9), README (M10), screenshots and AI docs (M11) and the video (M12). The plan treats those as first-class work, not end-of-week chores.

| ID | Criterion | Marks | What earns full marks |
| --- | --- | --- | --- |
| M1 | Project structure | 10 | All five named files visible as modules or packages in a layered `app/` layout, mapped in the README; routes only call services |
| M2 | Event CRUD | 15 | All 5 endpoints persist to PostgreSQL; id, title, description, date, location, capacity |
| M3 | Registration endpoints | 8 | POST/GET `/events/{id}/registrations`, DELETE `/registrations/{id}` |
| M4 | Business rules | 7 | Duplicate → 409, full → 409, missing event → 404, all inside `services.py` |
| M5 | Pydantic validation | 10 | Separate Create / Update / Read schemas with `Field` constraints and validators |
| M6 | Status codes | 8 | 200, 201, 204, 401, 404, 409, 422 with one consistent error shape |
| M7 | Swagger docs | 5 | Tags, summaries, descriptions, response models, example payloads |
| M8 | Code quality | 10 | Module/class/function docstrings, comments, PEP 8 (ruff), no duplication |
| M9 | Git practice | 10 | Public repo, one feature branch per feature, small meaningful commits, merges into `main` |
| M10 | README + requirements.txt | 4 | Newcomer can install, configure PostgreSQL, run app and tests |
| M11 | Screenshots + AI docs | 3 | A Swagger screenshot per endpoint; prompts, chat history, tools, settings |
| M12 | Demo video | 10 | Every required point covered, with you explaining the code yourself |
| B1 | Pagination | 3 | `skip`/`limit` on both list endpoints with defaults and bounds |
| B2 | Search & filter | 3 | `title` (partial, case-insensitive) + `date`, combinable with pagination |
| B3 | JWT auth | 5 | Hashed passwords, secret from `.env`, writes return 401 without token, reads public |
| B4 | Async DB | 4 | Async engine + `AsyncSession` end to end, no sync calls |
| B5 | pytest | 5 | Success and failure paths for every endpoint, all passing, run steps in README |

Two rubric traps to avoid: M4 wants the rules in `services.py` (not in routes), and M11 needs your full Claude Code prompts and chat history, so keep a prompt log from minute one.

## Tech stack and architecture

Use a layered `app/` package — config, database, models, schemas, services and API routes in separate modules — the layout of FastAPI's official full-stack template and most production services. The brief grades five named files (M1), so each keeps its name as a module or package, and the README maps them (table below the tree).

| Concern | Choice | Why |
| --- | --- | --- |
| Python & packaging | Python 3.12 managed by `uv` | Already installed; `uv run` works the same in PowerShell and in the video |
| Web framework | `fastapi[standard]` | Brings `fastapi dev`, Uvicorn and `python-multipart` (needed for the login form) |
| Database | Neon serverless PostgreSQL (free plan) | Nothing to install; the Neon console's Tables view and SQL Editor show data live in the demo (M12), and a branch gives tests their own database |
| ORM | SQLAlchemy 2.0 async + `asyncpg` driver | Required for B4; `Mapped[...]` typed models read well on camera |
| Migrations | Alembic, async template | Versioned schema changes instead of `create_all`; standard in production |
| Settings | `pydantic-settings` reading `.env` | Keeps the JWT secret and DB URL out of code (B3 asks for no hard-coded secret) |
| Auth | `PyJWT` + `pwdlib[argon2]` | The pairing current FastAPI docs use; avoids the unmaintained passlib |
| Tests | `pytest`, `pytest-asyncio`, `httpx` (`AsyncClient` + `ASGITransport`) | Async tests against a separate PostgreSQL test database |
| Lint/format | `ruff` (check + format) | One command for PEP 8 and import order (M8) |

```text
event-management-app/
├── app/
│   ├── __init__.py
│   ├── main.py                  # create_app(): middleware, routers, exception handlers
│   ├── db.py                    # async engine, session factory, Base, get_db()
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings, .env)
│   │   ├── security.py          # password hashing, JWT encode/decode
│   │   └── exceptions.py        # domain exceptions (EventNotFoundError, ...)
│   ├── models/                  # SQLAlchemy ORM, one module per table
│   │   ├── __init__.py          # re-exports User, Event, Registration
│   │   ├── user.py
│   │   ├── event.py
│   │   └── registration.py
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── common.py            # ErrorResponse, pagination params
│   │   ├── user.py              # UserCreate, UserRead, Token
│   │   ├── event.py
│   │   └── registration.py
│   ├── services/                # business logic, no FastAPI imports
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── event_service.py
│   │   └── registration_service.py
│   └── api/
│       ├── deps.py              # SessionDep, CurrentUser dependencies
│       └── routes/
│           ├── auth.py
│           ├── events.py
│           └── registrations.py
├── alembic/                     # migrations; env.py uses the async engine
├── alembic.ini
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_events.py
│   └── test_registrations.py
├── frontend/                    # React + Vite + Tailwind + shadcn/ui
├── docs/                        # screenshots/, ai-logs/, AI_USAGE.md
├── CLAUDE.md
├── .env.example
├── pyproject.toml / uv.lock
├── requirements.txt
└── README.md
```

Map the brief's five files to the new layout in the README and in video segment 2, so the grader finds each one at once:

| File the brief names | Where it lives | Holds |
| --- | --- | --- |
| `db.py` | `app/db.py` | Engine, session factory, `Base`, `get_db()` |
| `models.py` | `app/models/` | One ORM module per table |
| `schemas.py` | `app/schemas/` | Request and response models per resource |
| `services.py` | `app/services/` | All business rules, one service per resource |
| `main.py` | `app/main.py` + `app/api/routes/` | App factory, plus thin routers per resource |

> Diagram (see the plan doc): request flow — Client → api/routes/ → services/ → models/ + db.py → PostgreSQL (Neon); schemas/ validates input/output; domain errors return to the handler in main.py → 404/409.

A request enters a router in `app/api/routes/`, is validated by `app/schemas/`, and is handed to `app/services/`; any broken rule comes back as a domain error that the handler in `app/main.py` turns into 404 or 409.

Dependencies point one way: `api/routes` → `services` → `models` → `db`, with `core` usable by all. Routes parse the request, call one service function and return its result. Services raise exceptions from `core/exceptions.py` and never import FastAPI; one handler registered in `main.py` turns them into 404/409 JSON. That keeps routes thin (M1), rules in services (M4) and error shapes consistent (M6). There is no separate repository layer: with three tables, services querying through `AsyncSession` stay clean and are easier to explain on camera.

Schema changes go through Alembic: `uv run alembic revision --autogenerate -m "add events table"`, then `uv run alembic upgrade head`, one migration in each branch that changes models. Tests skip migrations and build tables with `Base.metadata.create_all` on the test database for speed.

### Neon specifics

- Use two Neon branches: `production (Neon's default)` for development and `test` for pytest, each with its own connection string (`DATABASE_URL`, `TEST_DATABASE_URL`). Tests can never touch dev data, which is a good point to make in the video.
- Use the direct endpoint (hostname without `-pooler`). The pooled endpoint runs PgBouncer, which can clash with asyncpg's prepared-statement cache; a direct connection is simpler and plenty for this app.
- Neon's string ends in `?sslmode=require&channel_binding=require`, and asyncpg rejects `sslmode`. `db.py` must switch the scheme to `postgresql+asyncpg://`, drop those query parameters and pass `connect_args={"ssl": "require"}`. Skipping this causes most first-run connection errors.
- Neon suspends idle compute after a few minutes, and the first query afterwards waits briefly while it wakes. `pool_pre_ping=True` and `pool_recycle=300` stop the app reusing a connection Neon has closed.
- Alembic reads the same Settings, so `alembic upgrade head` targets the `production` branch; tests build their own tables on `test`.

## Data model and API contract

Three tables and twelve endpoints. Lock this contract before any code, and paste it into `CLAUDE.md` so Claude Code never invents its own.

### Tables (`models.py`)

| Table | Columns | Constraints |
| --- | --- | --- |
| `users` | id, email, full\_name, hashed\_password, created\_at | email unique |
| `events` | id, title, description, event\_date (date), location, max\_capacity, created\_by → users.id, created\_at, updated\_at | capacity > 0 (CHECK); relationship to registrations with `cascade="all, delete-orphan"` |
| `registrations` | id, event\_id → events.id, user\_id → users.id, registered\_at | `UniqueConstraint(event_id, user_id)`; `ondelete="CASCADE"` |

The unique constraint is a safety net. The service checks for a duplicate first so it can return a clear 409 message, and it locks the event row (`SELECT … FOR UPDATE`) before counting seats, so two simultaneous sign-ups cannot overfill an event. Both are good "implementation decision" talking points for the video.

### Schemas (`schemas.py`)

- `EventCreate`: title (stripped, 1–200 chars), description (optional, ≤ 2000), event\_date (`date`, not in the past), location (1–200), max\_capacity (`gt=0`, `le=10000`).
- `EventUpdate`: same fields, all optional; the service applies `model_dump(exclude_unset=True)`.
- `EventRead`: all columns plus computed `registered_count` and `seats_left`; `from_attributes=True`.
- Registration has no request body: the registrant is the logged-in user from the token, and a non-positive or non-integer event id is rejected with 422. `RegistrationRead`: id, event\_id, registered\_at, plus the user's name and email.
- `UserCreate`, `UserRead`, `Token`, `ErrorResponse` (`{"detail": str}`), each with a `json_schema_extra` example for Swagger (M7).

### Endpoints (`main.py`)

| Method | Path | Auth | Success | Error codes |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | public | 201 | 409 email taken, 422 |
| POST | `/auth/login` | public (OAuth2 form) | 200 + token | 401 bad credentials |
| GET | `/auth/me` | token | 200 | 401 |
| POST | `/events` | token | 201 | 401, 422 |
| GET | `/events?skip&limit&title&date` | public | 200 | 422 bad params |
| GET | `/events/{id}` | public | 200 | 404 |
| PUT | `/events/{id}` | token | 200 | 401, 404, 409 capacity below current sign-ups, 422 |
| DELETE | `/events/{id}` | token | 204 | 401, 404 |
| POST | `/events/{id}/registrations` | token | 201 | 401, 404 no event, 409 duplicate, 409 full, 422 |
| GET | `/events/{id}/registrations?skip&limit` | token | 200 | 401, 404 |
| DELETE | `/registrations/{id}` | token (own registration only) | 204 | 401, 403 not yours, 404 |
| GET | `/health` | public | 200 | — |

Pagination: `skip` ≥ 0 (default 0), `limit` 1–100 (default 10), on both list endpoints (B1). Filters: `title` uses `ILIKE '%…%'`, `date` matches `event_date` exactly, and both combine with pagination (B2). Using `OAuth2PasswordBearer(tokenUrl="/auth/login")` makes Swagger's Authorize button work, which you will use on camera.

## Git and GitHub workflow

One branch per feature, merged into `main` through a GitHub pull request with a merge commit, so the grader sees every branch in the network graph (M9). Each branch carries its own tests, so `main` is green after every merge.

| # | Branch | Delivers | Typical commits |
| --- | --- | --- | --- |
| 0 | `main` | uv scaffold, `.gitignore`, `.gitattributes`, `CLAUDE.md`, README stub | `chore: initialise project with uv` |
| 1 | `feature/project-setup` | `db.py`, settings, `.env.example`, lifespan, `/health` | `feat(db): add async engine and session dependency` |
| 2 | `feature/event-crud` | Event model, schemas, services, 5 routes, test fixtures | `feat(events): add create and list endpoints`, `test(events): cover CRUD happy paths` |
| 3 | `feature/validation-error-handling` | Field constraints, domain exceptions, handlers | `feat(errors): map domain exceptions to 404/409` |
| 4 | `feature/jwt-auth` | User model, register/login/me, protected event writes | `feat(auth): protect event writes with bearer token` |
| 5 | `feature/pagination-filtering` | `skip`/`limit`, `title`, `date` | `feat(events): add case-insensitive title filter` |
| 6 | `feature/registrations` | Registration model, 3 login-protected routes, 3 business rules | `feat(registrations): block duplicate sign-ups with 409` |
| 7 | `feature/api-docs` | Tags, summaries, examples, response docs | `docs(api): add examples and error responses to OpenAPI` |
| 8 | `feature/frontend` | React + Vite app in `frontend/` | `feat(frontend): add event list and registration form` |
| 9 | `docs/submission` | README, requirements.txt, screenshots, AI\_USAGE.md | `docs: add setup, database and test instructions` |

Rules to give Claude Code (and to follow yourself):

- Start each branch from an up-to-date `main`: `git switch main`, `git pull`, `git switch -c feature/<name>`.
- Commit after each working step, 3–6 commits per branch, Conventional Commit messages. Never one giant commit.
- Run `uv run ruff check .`, `uv run ruff format .` and `uv run pytest` before the last commit on a branch.
- Push, open a PR with `gh pr create --fill`, merge with "Create a merge commit", then delete the branch.
- Never commit `.env`. On Windows, add `* text=auto` to `.gitattributes` to stop line-ending noise in diffs.
- Tag the final state `v1.0.0` on `main` before the deadline.

## Phase-by-phase build plan

Ten phases, each one branch, one Claude Code session and one recording clip. In every phase: plan mode first (Shift+Tab), read the plan aloud, approve, let it build, run the checks, then ask it to explain the new code before you merge.

### Phase 0 — Environment (manual, PowerShell)

In the Neon console (off camera, because it shows passwords): create a project named `event-management-app` in the region closest to you (Singapore is nearest to Pakistan). Keep the default `production` branch for development, then create a branch named `test`. Copy each branch's direct (non-pooled) connection string into `.env` as `DATABASE_URL` and `TEST_DATABASE_URL`.

```powershell
cd D:\development\iec35
uv init event-management-app --python 3.12
cd event-management-app
uv add "fastapi[standard]" "sqlalchemy[asyncio]" asyncpg pydantic-settings pyjwt "pwdlib[argon2]" alembic
uv add --dev pytest pytest-asyncio httpx ruff
git init -b main
gh repo create event-management-app --public --source . --remote origin
```

Then copy in the `CLAUDE.md` delivered with this plan, commit it on `main`, push, and start `claude` in the folder. Done when `uv run python -c "import fastapi, sqlalchemy, asyncpg"` succeeds and the repo is public on GitHub.

### Phase 1 — `feature/project-setup`

```text
Read CLAUDE.md. Create branch feature/project-setup. Build app/core/config.py with a pydantic-settings Settings class (DATABASE_URL, TEST_DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES) loaded from .env. Build app/db.py with an async engine for Neon (switch the URL to postgresql+asyncpg, drop the sslmode and channel_binding query params, pass connect_args={"ssl": "require"}, pool_pre_ping=True, pool_recycle=300), async_sessionmaker with expire_on_commit=False, a DeclarativeBase, and an async get_db() dependency. Initialise Alembic with the async template (alembic init -t async alembic), wired to Settings and Base. Build app/main.py with a create_app() factory and a GET /health route. Create the empty packages from the CLAUDE.md tree. Add .env.example and .gitignore entries. Docstrings on every module, class and function. Show me the plan first, then commit in small steps.
```

Done when `uv run fastapi dev app/main.py` starts and `/docs` shows `/health`.

### Phase 2 — `feature/event-crud`

```text
Create branch feature/event-crud from main. Add the Event model, EventCreate/EventUpdate/EventRead schemas, and async service functions create_event, list_events, get_event, update_event, delete_event exactly as the contract in CLAUDE.md. Put them in app/models/event.py, app/schemas/event.py, app/services/event_service.py and app/api/routes/events.py; routes must only call services. Generate and apply an Alembic migration. Return 201 on create, 204 on delete. Then add tests/conftest.py using TEST_DATABASE_URL (the Neon test branch), an httpx AsyncClient with ASGITransport and a get_db override, plus tests for all five endpoints. Run pytest and fix failures before committing.
```

Done when all CRUD tests pass and a created event appears in the Neon console's Tables view.

### Phase 3 — `feature/validation-error-handling`

```text
Create branch feature/validation-error-handling. Add Field constraints and validators from CLAUDE.md (stripped non-empty title, capacity gt=0, event_date not in the past on create). Add domain exceptions in app/core/exceptions.py (EventNotFoundError, RegistrationNotFoundError, DuplicateRegistrationError, EventFullError, CapacityBelowRegistrationsError) and one exception handler registered in app/main.py that maps them to 404/409 with {"detail": message}. Add tests for every 404, 409 and 422 case.
```

### Phase 4 — `feature/jwt-auth`

```text
Create branch feature/jwt-auth. Add a User model in app/models/user.py and an Alembic migration. Password hashing with pwdlib argon2 and JWT create/decode with PyJWT in app/core/security.py, login logic in app/services/auth_service.py. Add POST /auth/register, POST /auth/login (OAuth2PasswordRequestForm) and GET /auth/me. Protect POST, PUT and DELETE /events with a CurrentUser dependency in app/api/deps.py that returns 401 with a WWW-Authenticate header; keep the GET /events routes public. Store created_by on events. Add an auth_headers fixture and 401 tests.
```

Auth now comes before registrations, because registering for an event requires login. Done when the Swagger Authorize button logs in and event writes return 401 without it.

### Phase 5 — `feature/pagination-filtering`

```text
Create branch feature/pagination-filtering. Add skip (>=0, default 0) and limit (1-100, default 10) to GET /events as a reusable PaginationParams dependency (Phase 6 reuses it for registrations), plus title (ILIKE, case-insensitive partial) and date filters on GET /events, combinable with pagination. Order results by event_date then id so pages are stable. Add tests for bounds, filters and combinations.
```

### Phase 6 — `feature/registrations`

```text
Create branch feature/registrations. Add the Registration model (event_id, user_id, registered_at) with a unique (event_id, user_id) constraint, cascade delete and an Alembic migration. All three registration routes require login through CurrentUser: POST /events/{id}/registrations registers the logged-in user (no request body; the event id must be a positive integer); GET /events/{id}/registrations lists registrations with each user's name and email, paginated with the PaginationParams dependency; DELETE /registrations/{id} lets a user cancel only their own registration (add NotRegistrationOwnerError mapped to 403). In app/services/registration_service.py, lock the event row with with_for_update, then enforce: event exists (404), user not already registered (409), seats left (409). Add seats_left and registered_count to EventRead. Write tests for each rule, including filling an event to capacity with several users, 401 without a token and 403 on someone else's registration.
```

Done when Swagger shows each rule: 401 without login, 404 for a missing event, 409 on a second sign-up, 409 when full, 403 on someone else's registration.

### Phase 7 — `feature/api-docs`

```text
Create branch feature/api-docs. For every route add tags, summary, description, response_model, status_code and responses={404/409/401: {"model": ErrorResponse}}. Add json_schema_extra examples to every request schema. Set app title, version and description. Do not change behaviour; run the full test suite.
```

### Phase 8 — `feature/frontend` (React + Vite)

Stack: React + Vite + TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, React Router, react-hook-form + zod, lucide-react icons. Needs Node.js LTS (`node -v`). Budget one day and build it only after Phase 7 is merged; it earns no marks itself but makes the demo far clearer.

```text
Read the Frontend section of CLAUDE.md. Create branch feature/frontend. Scaffold a React + Vite + TypeScript app in frontend/ (npm create vite@latest frontend -- --template react-ts). Add Tailwind CSS v4 via @tailwindcss/vite and the @ path alias, then initialise shadcn/ui and add button, card, input, label, table, dialog, alert-dialog, form, badge, calendar, popover and sonner. Install @tanstack/react-query, react-router-dom, react-hook-form, zod and @hookform/resolvers.

Read the running backend's /openapi.json and write typed API functions in src/lib/api.ts, base URL from VITE_API_URL (default http://127.0.0.1:8000). Keep the JWT in an AuthContext backed by localStorage and send it as a Bearer header; on 401, log out and go to /login.

Pages: Login and Register; Events list with title search, date filter and Previous/Next pagination, with Create, Edit and Delete shown only when logged in; Event detail with a seats-left badge, the registrations list with Cancel, and Register / Cancel my registration buttons for logged-in users. Zod schemas mirror the Pydantic rules. Show every API error's detail message in a sonner toast.

Backend: add CORSMiddleware in app/main.py allowing http://localhost:5173, with the origin in Settings.

Look: clean and minimal, neutral theme with one accent colour, responsive, empty and loading states on every list. Show me the plan first, then commit in small steps. Run npm run build before the last commit.
```

Done when both servers run (`uv run fastapi dev app/main.py` and `npm run dev` in `frontend/`), the full flow works in the browser, `npm run build` has no type errors, and registering twice shows the 409 message as a toast.

### Phase 9 — `docs/submission`

```text
Create branch docs/submission. Write README.md: overview, tech stack, project structure, prerequisites, uv setup, Neon setup (project, production and test branches, direct connection strings), .env configuration, run commands, test commands, endpoint table and screenshots section. Run uv export --format requirements-txt --no-hashes -o requirements.txt. Create docs/AI_USAGE.md with tools, model, settings and links to the exported chat logs.
```

After every phase, before merging, ask: `Explain the functions you added in this phase, the business rule each enforces and why, as if I am presenting it.` Those answers become your video notes.

## Testing strategy

Tests run against the Neon `test` branch (`TEST_DATABASE_URL`), never the dev branch and never SQLite, so `ILIKE`, row locks and constraints behave exactly as in production. Target: about 40 tests, every one passing, run on camera with `uv run pytest -v`.

Setup in `conftest.py` and `pyproject.toml`:

- `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "session"`.
- Test engine built with `poolclass=NullPool`; this avoids the "attached to a different event loop" error common with asyncpg.
- Create tables once per session, then truncate them (RESTART IDENTITY CASCADE) before each test. Dropping tables per test would cost several round trips to Neon each time; truncating keeps the suite fast and every test still starts empty.
- Override `get_db` with `app.dependency_overrides`; client is `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
- Fixtures: `client`, `auth_headers` (registers and logs in a user), `event` (a future-dated event built from `date.today() + timedelta(days=30)` so tests never expire).

| File | Success cases | Failure cases |
| --- | --- | --- |
| `test_events.py` | create 201, list 200, get 200, update 200, delete 204, pagination, title and date filters | empty title 422, capacity 0 422, past date 422, missing field 422, unknown id 404, no token 401, capacity below sign-ups 409 |
| `test_registrations.py` | register 201, list 200, cancel 204, seat freed after cancel | unknown event 404, duplicate sign-up 409, full event 409, no token 401, cancelling another user's registration 403, unknown registration 404 |
| `test_auth.py` | register 201, login 200 with token, `/auth/me` 200 | duplicate email 409, wrong password 401, bad or expired token 401 |

The brief withholds marks for tests that were written but not run, so show the green `pytest -v` output in the video and paste the summary line into the README.

## Recording plan

You are making two recordings: the long development process (your AI-usage evidence for M11) and a separate, edited demo video of about 18 minutes (M12). Record the process as one Camtasia clip per phase, so a mistake costs one clip, not the whole session.

### Before each recording session

- Windows Focus Assist on, so no notifications appear on screen.
- VS Code font 16–18, terminal font 16, 1920×1080 resolution, one monitor captured.
- Never open `.env` on camera; if it slips into view, blur it in Camtasia before export. The same goes for Neon's connection-string dialog, which shows your database password; if it leaks on video, reset the password in Neon.
- Speak the intent before each prompt ("now I'm adding the capacity rule") — it makes the footage easy to cut later.
- At the end of each phase in Claude Code, run `/export` and save to `docs/ai-logs/phase-N.md`. These files are the chat history the brief asks for.

### Demo video script

| # | Segment | Min | What to show |
| --- | --- | --- | --- |
| 1 | Introduction | 1 | Acme Corp scenario, what the API does, tech stack |
| 2 | Project structure | 2 | Folder tree; how a request flows `main.py` → `services.py` → `models.py` → PostgreSQL, and `schemas.py` at both edges |
| 3 | Database integration | 2 | `db.py` engine and session; tables and rows in the Neon console before and after a request; the separate test branch |
| 4 | Business logic | 4 | Registration service: row lock, duplicate check, capacity check, domain exceptions and the handler; validators in `schemas.py`; JWT dependency |
| 5 | App running | 1 | `uv run fastapi dev app/main.py`, `/docs` loading |
| 6 | Endpoint testing | 5 | Swagger: register, login, Authorize, full CRUD, filters and paging, registrations, then 401, 404, 409 and 422 on purpose |
| 7 | Automated tests | 1.5 | `uv run pytest -v`, all green |
| 8 | Key decisions | 1 | Async end to end, Neon branch for tests, login-required registration, partial PUT, argon2 |
| 9 | Frontend | 1 | Create an event and register through the page while the Neon console updates |
| 10 | Git history | 0.5 | GitHub branches, merged PRs, network graph |

Rehearse segment 4 once without recording. It is where graders judge whether you understand the code, and it should be in your own words, not read from Claude's explanation.

Take the Swagger screenshots (M11) during segment 6 rehearsal: one PNG per endpoint showing request and response, saved to `docs/screenshots/` with names like `03-post-events-201.png`.

## Schedule and submission checklist

All code is merged by Sunday 15 Nov, leaving two days for documentation and the video and Wednesday as buffer.

| Day | Work | Branches merged by end of day |
| --- | --- | --- |
| Wed 11 Nov | Phase 0 + 1: environment, repo, `db.py`, `/health` | `feature/project-setup` |
| Thu 12 Nov | Phase 2 + 3: event CRUD, validation, error handling | `feature/event-crud`, `feature/validation-error-handling` |
| Fri 13 Nov | Phase 4 + 5: JWT auth, pagination, filters | `feature/jwt-auth`, `feature/pagination-filtering` |
| Sat 14 Nov | Phase 6: registrations (login required) | `feature/registrations` |
| Sun 15 Nov | Phase 7 + 8: Swagger polish, frontend | `feature/api-docs`, `feature/frontend` |
| Mon 16 Nov | Phase 9: README, requirements.txt, screenshots, AI\_USAGE.md | `docs/submission` |
| Tue 17 Nov | Rehearse, record and edit the demo video | — |
| Wed 18 Nov | Fresh-clone test, tag `v1.0.0`, submit before evening | — |

### Final checklist

- [ ] Fresh clone on a clean folder: `uv sync`, create `.env`, `uv run fastapi dev app/main.py` works by following the README only
- [ ] `uv run pytest -v` all green; summary line pasted in README
- [ ] `uv run ruff check .` clean; docstrings on every module, class and function
- [ ] No business logic in `main.py`; all three registration rules live in `services.py`
- [ ] `requirements.txt` regenerated after the last dependency change
- [ ] One Swagger screenshot per endpoint in `docs/screenshots/`
- [ ] `docs/AI_USAGE.md` lists tools, model, settings and every exported chat log
- [ ] Repo is public; all feature branches visible as merged PRs
- [ ] Demo video covers all 10 segments and is uploaded with a working link
- [ ] Submission includes the repo link, video link and AI usage docs
