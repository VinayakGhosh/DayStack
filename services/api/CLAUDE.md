# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**proj-task** (v0.3.2) is a SaaS task management REST API with subscription-based access control. Built with FastAPI + PostgreSQL, it enforces per-plan usage limits (project counts, daily task creation limits) and supports multi-tenant organizations.

## Commands

### Development

```bash
# Start database (PostgreSQL 17 via Docker)
docker compose up -d

# Run with hot reload
uvicorn main:app --reload
# OR use the startup script:
./start.sh

# Install dependencies
pip install -r requirements.txt          # Windows
pip install -r requirements-linux.txt   # Linux/Docker
```

### Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (auto-generate from model changes)
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

### Docker

```bash
docker build -t proj-task .
docker run -p 8000:8000 proj-task
```

API docs available at `http://localhost:8000/docs` when running.

## Architecture

### Layer Structure

```
routes/      → FastAPI route handlers (request parsing, response shaping)
lib/         → Shared dependencies injected into routes (auth, subscription checks)
schema/      → Pydantic models for request validation and response serialization
models/      → SQLAlchemy ORM table definitions
db/db.py     → Engine, session factory, and get_db() dependency
scheduler.py → APScheduler job: daily subscription expiry check
main.py      → App factory: registers routers, lifespan (scheduler + default plan seeding)
```

### Authentication & Authorization

`lib/auth.py` provides `get_current_user()` as a FastAPI dependency. All protected routes inject this. Two roles exist: `GENERAL` and `ADMIN`.

JWT tokens: short-lived access tokens + long-lived refresh tokens. Configured via `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` env vars.

### Subscription Enforcement

`lib/subscription.py` provides `require_active_subscription()` as a dependency. Routes that are gated by plan tier inject this alongside `get_current_user()`.

Usage limits are tracked in the `usage` table (per user, per feature, per day). The `plans` table defines `max_projects` and `task_per_day` limits per tier. When a subscription expires, the scheduler downgrades the user to the Free plan.

### Soft Deletes

Projects and Tasks use an `isDelete` boolean flag — records are never hard-deleted. All list queries must filter `isDelete == False`.

### Key Models

- `users` + `subscriptions` + `usage` → in `models/user.py`
- `plans` + `projects` + `tasks` → in `models/plan.py`
- `organizations` + `organization_members` + `organization_invitations` → in `models/organization.py`

### Database Connection

`db/db.py` uses SQLAlchemy with `pool_size=30`, `max_overflow=10`, `pool_recycle=300`, and `pool_pre_ping=True`. The `get_db()` generator yields sessions for route-level dependency injection.

## Environment Variables

Copy `.env-sample` to `.env`. Required variables:

```
DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME
SECRET_KEY, ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
DEFAULT_PLANS   # CSV of plan names to seed on startup, e.g. "Free, Pro"
SENTRY_DSN      # Optional, for error monitoring
```

## Route Registration

All routes are versioned under `/v1`. The `routes/__init__.py` aggregates sub-routers, which `main.py` mounts. When adding a new route file, register it in `routes/__init__.py`.
