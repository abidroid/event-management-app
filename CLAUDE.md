# CLAUDE.md — Corporate Event Management API

Backend REST API for Acme Corp's internal event system (university assignment,
graded by a rubric). FastAPI + PostgreSQL + SQLAlchemy 2.0 async + Pydantic v2 + JWT.
Deadline: Wed 18 Nov 2026. The developer must be able to explain every line, so
prefer clear, conventional code over clever code.

## Environment
- Windows 11, PowerShell. Python 3.12 managed by `uv`. Always run tools via `uv run`.
- Run app:      `uv run fastapi dev app/main.py`  -> http://127.0.0.1:8000/docs
- Run tests:    `uv run pytest -v`
- Lint/format:  `uv run ruff check . --fix` and `uv run ruff format .`
- Add a dependency: `uv add <pkg>` (dev: `uv add --dev <pkg>`), then
  `uv export --format requirements-txt --no-hashes -o requirements.txt`
- Migrations: `uv run alembic revision --autogenerate -m "<msg>"` then `uv run alembic upgrade head`
- Database: Neon serverless PostgreSQL. Branch `main` = dev (`DATABASE_URL`),
  branch `test` = pytest (`TEST_DATABASE_URL`). Use the DIRECT endpoint (no `-pooler`).
- Neon strings end in `?sslmode=require&channel_binding=require`; asyncpg rejects these.
  db.py must convert the scheme to `postgresql+asyncpg://`, strip those query params and pass
  `connect_args={"ssl": "require"}`. Engine: `pool_pre_ping=True`, `pool_recycle=300`
  (Neon suspends idle compute and closes connections).
- Config comes from `.env` via pydantic-settings. Never commit `.env`, never print its values
  or connection strings (the developer is screen-recording).

## Project structure (industry-standard layered layout)
```
app/
  main.py                 create_app(): CORS, routers, exception handlers, /health
  db.py                   async engine, async_sessionmaker(expire_on_commit=False), Base, get_db()
  core/
    config.py             Settings (pydantic-settings, .env)
    security.py           pwdlib argon2 hashing, PyJWT encode/decode
    exceptions.py         domain exceptions
  models/                 one module per table: user.py, event.py, registration.py
                          (__init__.py re-exports all models so Alembic sees them)
  schemas/                common.py (ErrorResponse, pagination), user.py, event.py, registration.py
  services/               auth_service.py, event_service.py, registration_service.py
  api/
    deps.py               SessionDep, CurrentUser (Annotated dependencies)
    routes/               auth.py, events.py, registrations.py (APIRouter each)
alembic/  alembic.ini     migrations (async template)
tests/                    conftest.py, test_auth.py, test_events.py, test_registrations.py
frontend/                 React + Vite + TypeScript app (see Frontend section)
docs/                     screenshots/, ai-logs/, AI_USAGE.md
```
- The brief grades five named files. Keep the names recognisable and maintain this mapping
  in the README: db.py -> app/db.py, models.py -> app/models/, schemas.py -> app/schemas/,
  services.py -> app/services/, main.py -> app/main.py + app/api/routes/.
- Absolute imports from the package root: `from app.models import Event`.
- No repository layer: services query through AsyncSession directly.

## Layering rules
- Dependency direction: api/routes -> services -> models -> db; core is shared by all.
- Routes in `app/api/routes/` only: parse input, call ONE service function, return its result.
  No queries, no business rules, no `if` checks on data in routes.
- Services raise domain exceptions from `app/core/exceptions.py` (`EventNotFoundError`, `RegistrationNotFoundError`,
  `DuplicateRegistrationError`, `EventFullError`, `CapacityBelowRegistrationsError`,
  `EmailAlreadyRegisteredError`, `InvalidCredentialsError`). Services never import `HTTPException`.
- One exception handler registered in `app/main.py` maps domain exceptions to 404 / 409 / 401 with body
  `{"detail": "<human-readable message>"}`.
- Everything async: `AsyncSession`, `await session.execute(select(...))`. No sync DB calls.

## Data model
- users: id, email (unique), full_name, hashed_password, created_at
- events: id, title, description, event_date (date), location, max_capacity (CHECK > 0),
  created_by -> users.id, created_at, updated_at; registrations relationship with
  cascade="all, delete-orphan"
- registrations: id, event_id -> events.id (ondelete CASCADE), employee_name,
  employee_email, registered_at; UniqueConstraint(event_id, employee_email)

## Validation (app/schemas/)
- EventCreate: title stripped 1-200, description optional <=2000, event_date not in past,
  location 1-200, max_capacity gt=0 le=10000
- EventUpdate: same fields all optional; service applies model_dump(exclude_unset=True)
- EventRead: all columns + registered_count + seats_left; from_attributes=True
- RegistrationCreate: employee_name 1-100, employee_email EmailStr
- Every request schema has a json_schema_extra example.

## API contract
| Method | Path | Auth | Success | Errors |
|---|---|---|---|---|
| POST | /auth/register | public | 201 | 409, 422 |
| POST | /auth/login (OAuth2PasswordRequestForm) | public | 200 token | 401 |
| GET | /auth/me | token | 200 | 401 |
| POST | /events | token | 201 | 401, 422 |
| GET | /events?skip&limit&title&date | public | 200 | 422 |
| GET | /events/{id} | public | 200 | 404 |
| PUT | /events/{id} | token | 200 | 401, 404, 409 (capacity below sign-ups), 422 |
| DELETE | /events/{id} | token | 204 | 401, 404 |
| POST | /events/{id}/registrations | public | 201 | 404, 409 duplicate, 409 full, 422 |
| GET | /events/{id}/registrations?skip&limit | public | 200 | 404 |
| DELETE | /registrations/{id} | public | 204 | 404 |
| GET | /health | public | 200 | - |

- Pagination: skip >= 0 default 0; limit 1-100 default 10. Order by event_date, id.
- title filter: ILIKE '%value%'; date filter: exact match on event_date; combinable.
- Registration service: lock the event row with `.with_for_update()`, then check
  exists (404) -> duplicate email (409) -> seats left (409), then insert.
- Auth: PyJWT (HS256, secret from settings), pwdlib argon2 hashing,
  OAuth2PasswordBearer(tokenUrl="/auth/login"); 401 includes WWW-Authenticate: Bearer.
- Every route has tags, summary, description, response_model, status_code and
  `responses=` for its error codes using ErrorResponse.

## Code quality (graded)
- Docstring on every module, class and function (Google style: Args / Returns / Raises).
- Comments explain WHY, not what. Meaningful names. PEP 8 via ruff. No duplication:
  shared lookups go in helpers like `_get_event_or_raise()`.
- Type hints everywhere.

## Testing
- Tests build tables with Base.metadata.create_all (no migrations).
- Neon `test` branch via TEST_DATABASE_URL, engine with NullPool. Create tables once per
  session; TRUNCATE all tables RESTART IDENTITY CASCADE before each test (dropping per test
  is slow over the network). `get_db` overridden, httpx AsyncClient + ASGITransport.
- pytest config: asyncio_mode = "auto", asyncio_default_fixture_loop_scope = "session".
- Test dates are relative (`date.today() + timedelta(days=30)`), never hard-coded.
- Every endpoint gets success AND failure tests. Run the suite and make it pass before
  any commit that touches app code.

## Git workflow (graded)
- Never commit directly to main except the initial scaffold.
- One branch per feature: feature/project-setup, feature/event-crud,
  feature/validation-error-handling, feature/registrations, feature/pagination-filtering,
  feature/jwt-auth, feature/api-docs, feature/frontend, docs/submission.
- Small commits after each working step, Conventional Commits
  (`feat(events): ...`, `fix(...)`, `test(...)`, `docs(...)`, `chore(...)`).
- Before the last commit on a branch: ruff check, ruff format, pytest.
- Merge via `gh pr create --fill`, merge commit (not squash), delete branch.

## Frontend (frontend/, branch feature/frontend)
- Stack: React + Vite + TypeScript, Tailwind CSS v4 (@tailwindcss/vite), shadcn/ui,
  TanStack Query, React Router (react-router-dom), react-hook-form + zod (@hookform/resolvers),
  lucide-react, sonner toasts. Node.js LTS + npm. These are pre-approved dependencies.
- Run: `cd frontend; npm run dev` -> http://localhost:5173. Build check: `npm run build`.
- API base URL from `VITE_API_URL` in `frontend/.env` (default http://127.0.0.1:8000).
- Backend enables CORSMiddleware for http://localhost:5173 (origin held in Settings).
- Structure: src/lib/api.ts (typed fetch functions matching /openapi.json),
  src/context/AuthContext.tsx (JWT in localStorage, Bearer header, logout on 401),
  src/pages/ (LoginPage, RegisterPage, EventsPage, EventDetailPage), src/components/
  (EventFormDialog, RegistrationForm, ConfirmDeleteDialog, Pagination), src/components/ui/ (shadcn).
- Server state only through TanStack Query; invalidate queries after every mutation.
- Zod schemas mirror the Pydantic rules; every API error's `detail` shows in a toast.
- Look: clean and minimal, neutral theme, one accent colour, responsive, loading and
  empty states on every list. No business rules in the frontend beyond form validation.

## Working style
- Always present a plan first and wait for approval before editing files.
- After finishing a phase, summarise what changed and explain new functions simply.
- Ask before adding any dependency not listed above.
