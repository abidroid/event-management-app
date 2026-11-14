# AI Usage

This document records how AI was used to build the Corporate Event Management API:
the tools, the model, the settings, the prompts and the full chat history of every phase.

## Tools and model

| Item | Value |
| --- | --- |
| Tool | [Claude Code](https://claude.com/claude-code) CLI, v2.1.319 |
| Model | Claude Opus 5.5 (`claude-opus-5-5`) |
| Plan | Claude Pro |
| Environment | Windows 11, PowerShell, VS Code; Python 3.12 via `uv`, Node.js LTS for the frontend |
| Integrations | Git and the GitHub CLI (`gh`) for branches and pull requests |

## Settings

- **Project instructions: [`CLAUDE.md`](../CLAUDE.md).** Written before any code. It fixes the
  stack, folder layout, layering rules, data model, validation rules, the full API contract,
  testing approach, Git workflow and coding standards (docstrings, type hints, ruff), so the
  AI follows one agreed design instead of inventing its own.
- **Development plan: [`docs/DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md).** Splits the work into
  ten phases, one Git branch each, with the exact prompt used for each phase.
- **Plan mode before every phase.** Claude Code first produced a written plan without touching
  any file; I read it, asked for changes where needed and approved it before any code was written.
- **Default permission mode.** Every file edit and shell command had to be approved by me.
- **Persistent memory rules** added during development when I corrected the AI:
  - run `ruff check`, `ruff format --check`, a mypy type check and `pytest` before every pull
    request (added after PR #2, when my editor showed a mypy error that ruff and pytest missed);
  - `main` is protected and only changes through pull requests;
  - never delete branches on GitHub after merging, so the grader can see every branch.
- **Global settings** (`~/.claude/settings.json`): auto-updates on the latest channel,
  dark theme, full-screen terminal UI. No custom model parameters were changed.
- **Secrets.** `.env` was never opened on screen or committed; the AI was instructed in
  `CLAUDE.md` never to print connection strings or secret values.

## Workflow for every phase

1. Start Claude Code in the project folder and paste the phase prompt from the development plan.
2. Review the plan in plan mode, adjust it and approve it.
3. Let Claude Code build in small Conventional Commits on the feature branch.
4. Run the checks: `uv run ruff check .`, `uv run ruff format --check .`,
   `uv run --with mypy mypy app` and `uv run pytest -v` (plus `npm run build` for the frontend).
5. Ask: *"Explain the functions you added in this phase, the business rule each enforces and
   why, as if I am presenting it."* The answers became my notes for the demo video.
6. Open a pull request with `gh pr create --fill` and merge it with a merge commit.
7. Export the conversation with `/export` into `docs/ai-logs/`.

## Prompts and chat history

The full text of each prompt is in the
[phase-by-phase build plan](DEVELOPMENT_PLAN.md#phase-by-phase-build-plan). The exported
chat logs contain every prompt, every plan, every follow-up question and correction, and
all tool output.

| Phase | Branch | Prompt (summary) | Chat log |
| --- | --- | --- | --- |
| 1 | `feature/project-setup` | Settings, async `db.py` for Neon, Alembic async template, `create_app()` with `/health` | [phase-1.md](ai-logs/phase-1.md) |
| 2 | `feature/event-crud` | Event model, schemas, services and five CRUD routes; test fixtures on the Neon test branch | [phase-2.md](ai-logs/phase-2.md) |
| 3 | `feature/validation-error-handling` | Field constraints and validators, domain exceptions, one handler mapping to 404/409 | [phase-3.md](ai-logs/phase-3.md) |
| 4 | `feature/jwt-auth` | User model, argon2 hashing, PyJWT, register/login/me, protect event writes with 401 | [phase-4.md](ai-logs/phase-4.md) |
| 5 | `feature/pagination-filtering` | Reusable `skip`/`limit` dependency, `title` ILIKE and `date` filters, stable ordering | [phase-5.md](ai-logs/phase-5.md) |
| 6 | `feature/registrations` | Login-required registrations, row lock, 404/409/409 rules, 403 for others' registrations | [phase-6.md](ai-logs/phase-6.md) |
| 7 | `feature/api-docs` | Tags, summaries, descriptions, response models, error responses and examples in Swagger | [phase-7-api-docs.md](ai-logs/phase-7-api-docs.md) |
| 8 | `feature/frontend` | React + Vite + TypeScript client with shadcn/ui, TanStack Query and toasts for API errors | [phase-8-frontend.md](ai-logs/phase-8-frontend.md) |
| 9 | `docs/submission` | README, `requirements.txt` and this document | [phase-9-submission.md](ai-logs/phase-9-submission.md) |

## What I checked and decided myself

- I wrote the API contract, data model and phase plan before using the AI, and kept them
  in `CLAUDE.md` so every session worked from the same rules.
- I reviewed and approved every plan, edit and command, and asked for changes when a plan
  did not match the contract.
- I ran the checks myself after each phase and read the code before merging. Problems found
  this way, such as the mypy typing errors in PR #2, were fixed before the merge and turned
  into permanent rules for the AI.
- I asked the AI to explain every new function so I could explain the code myself in the
  demo video.
