# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

DayStack is a personal task-execution MVP: one Member owns Projects, organizes Tasks on a board, and picks up to three Tasks for Today. `docs/MVP_ARCHITECTURE.md` is the architectural authority; `CONTEXT.md` is the glossary. Use its terms (Member, Project, Task, Workflow status, Today, Label, Subtask, Attachment) in code, tests, and issues, and avoid the listed synonyms. "Task Factory" is legacy branding and must not appear in new member-facing copy or config.

## Layout

- `apps/web` — React 18 + TypeScript + Vite + shadcn-ui (Tailwind) client. Dev server on port 8080.
- `services/api` — FastAPI + SQLAlchemy + Alembic backend on PostgreSQL 17. See `services/api/CLAUDE.md` for backend structure and MVP rules.

## Commands

Frontend (from `apps/web`):

```bash
npm install
npm run dev                                   # http://localhost:8080
npm test                                      # vitest run (jsdom)
npx vitest run src/components/tasks/TaskCard.test.tsx   # single file
npx vitest run -t "test name substring"       # single test
npm run lint
npm run typecheck
npm run build                                 # typecheck + vite build
```

Copy `.env.example` to `.env`; `VITE_API_BASE_URL` points at the API (empty for same-origin deployments).

Backend (from `services/api`, Windows venv at `.venv`):

```bash
docker compose up -d                          # PostgreSQL only (container daystack-db)
alembic upgrade head
uvicorn main:app --reload                     # http://localhost:8000
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m unittest discover -s tests -p test_today.py -v   # single file
```

`sh start.sh` does compose + migrate + uvicorn in one step (Git Bash). Copy `.env-sample` to `.env`; `DATABASE_URL` wins over the `DATABASE_*` parts (`db/config.py`). Use `requirements.txt` on Windows and `requirements-linux.txt` for Linux/Docker. API tests run against in-memory SQLite and don't need the Postgres container, but migrations must be valid on PostgreSQL (see `docs/field-debug/` for a past migration that broke startup).

## Architecture across the stack

- **Task Workspace is the seam.** `services/api/task_workspace/` owns ownership checks, quotas (5 Projects, 30 non-completed Tasks per Project), the single completion Workflow status, Today (≤3 Tasks per Member-local date), and Attachment coordination. Routes in `routes/` are thin adapters and must not touch ORM models directly. Tests target the workspace first, then HTTP contracts.
- **HTTP contract.** Everything is under `/v1` (`sessions`, `project`, `tasks`, `today`, health). Collections return empty lists, not 404. Domain failures map to stable error codes (`project_limit_reached`, `task_limit_reached`, `today_limit_reached`, `status_in_use`, `forbidden`), and the frontend treats these as the source of truth.
- **Auth.** Email/password. Access and refresh tokens live in HTTP-only cookies and never in JS or localStorage. `apps/web/src/lib/api.ts` is the only transport: it sends `credentials: 'include'`, echoes the `daystack_csrf` cookie as `X-CSRF-Token`, deduplicates refreshes via `/v1/sessions/refresh`, and dispatches `daystack:session-expired`, which `AuthContext` listens for. Pages must not call `fetch` directly.
- **Completion is by flag, not name.** A Task is complete when its Workflow status has `is_completion`; never compare status names.
- **Dates.** Due dates are date-only, interpreted in the Member's saved IANA time zone (`apps/web/src/lib/dateOnly.ts` on the client). The browser time zone is only a signup default.
- **Attachments.** Blobs are stored in PostgreSQL during development (ADR 0001) and never appear in normal responses or frontend state. Images are normalized to WebP.
- **Deferred scope.** Billing, plans, subscriptions, organizations, sharing, comments, and recurrence have leftover models and migrations but are not mounted. Don't wire them into MVP paths.
- CORS origins come from `CORS_ALLOWED_ORIGINS`. Cookie behavior comes from `COOKIE_SECURE`, `COOKIE_SAME_SITE`, and `COOKIE_DOMAIN`.
- The web app version shown in the UI comes from `apps/web/package.json` (`src/lib/version.ts`).

## Agent skills

### Issue tracker

Issues and specs are tracked in GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

The repository uses the default five-role triage label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository with a root `CONTEXT.md` and ADRs in `docs/adr/`. See `docs/agents/domain.md`.
