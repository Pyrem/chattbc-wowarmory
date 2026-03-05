# chattbc.gg

TBC-era World of Warcraft armory and community platform with an AI-powered chatbot.

## Project Structure

Monorepo: `frontend/` (Next.js 14+, TypeScript), `backend/` (Python, FastAPI), `infra/` (AWS CDK + Lambdas), `e2e/` (Playwright), `shared/` (static TBC game data).

## Commands

```bash
# Backend
cd backend && uvicorn app.main:app --reload        # Dev server
cd backend && pytest                                 # Unit + integration tests
cd backend && pytest tests/unit                      # Unit tests only
cd backend && ruff check --fix . && ruff format .    # Lint + format
cd backend && mypy --strict app/                     # Type check
cd backend && alembic upgrade head                   # Run migrations
cd backend && alembic revision --autogenerate -m ""  # Generate migration

# Frontend
cd frontend && npm run dev          # Dev server (port 3000)
cd frontend && npm run build        # Production build
cd frontend && npx vitest           # Unit tests
cd frontend && npx eslint --fix .   # Lint
cd frontend && npx prettier --write . # Format

# Code quality (full chain - run before every commit)
make quality    # Runs: lint -> typecheck -> ast-grep -> semgrep -> tests (both backend + frontend)
make lint       # Ruff + ESLint + Prettier
make typecheck  # mypy --strict
make scan       # ast-grep + Semgrep
make test       # pytest + Vitest

# E2E
cd e2e && pytest                    # Playwright E2E tests

# Infrastructure
cd infra/cdk && cdk synth           # Synthesize CloudFormation
cd infra/cdk && cdk deploy          # Deploy to AWS

# Local dev environment
docker-compose up -d                # Postgres + Redis
```

## Code Style

### Python (backend/, infra/lambdas/, e2e/)
- Python 3.12+. Always use `async def` for FastAPI route handlers.
- All route handlers return Pydantic response models. Never return raw dicts.
- Type hints on all function signatures. mypy --strict must pass.
- Use `async with` for database sessions via the dependency injection pattern.
- Blizzard API calls go through `app/services/blizzard.py`, never raw httpx.
- Imports sorted by ruff (isort rules). One class per model file.

### TypeScript (frontend/)
- Strict mode. No `any` types without documented justification.
- React functional components only. Named exports, not default (except page.tsx/layout.tsx).
- Tailwind for all styling. No CSS modules, no styled-components.
- shadcn/ui for base components. Extend, don't reinvent.
- API calls go through `lib/api-client.ts`, never raw fetch in components.

## Mandatory Code Quality Pipeline

**All code must pass this pipeline before commit. No exceptions.**

### Python
1. `ruff check --fix . && ruff format .`
2. `mypy --strict app/`
3. `ast-grep scan -r ../rules/python/`
4. `semgrep --config=p/python --config=../.semgrep/`
5. `pytest` (relevant tests must pass, new code must include tests)
6. If any step produced fixes, restart from step 1.

### TypeScript
1. `npx eslint --fix .`
2. `npx prettier --write .`
3. `ast-grep scan -r ../rules/typescript/`
4. `semgrep --config=p/typescript --config=../.semgrep/`
5. `npx vitest run` (relevant tests must pass)
6. If any step produced fixes, restart from step 1.

## Architecture Decisions (read before making changes)

Before starting work, read the relevant docs:

- `docs/architecture.md` — Full system architecture, tech stack rationale, data flow, auth model
- `docs/conventions.md` — Coding patterns, error handling, file naming, testing patterns
- `docs/stories.md` — Feature backlog with acceptance criteria (Jira-compatible)
- `docs/data-models.md` — Database schema, relationships, migration patterns
- `docs/blizzard-api.md` — Blizzard API integration patterns, caching strategy, rate limits

## Key Architectural Rules

- **Two Blizzard API keys**: (1) Developer key (Client Credentials) for fetching armory data server-side. (2) OAuth client for optional user Battle.net linking. These are separate and must never be confused.
- **Auth is email-primary**: Users register/login with email+password. Battle.net OAuth is optional account linking for character ownership verification, not a login method.
- **Stale-while-revalidate caching**: Blizzard data is retained indefinitely. TTLs trigger re-fetch, not deletion. Serve stale data instantly, refresh in background.
- **Layered backend**: Routers → Services → Models. Routers handle HTTP. Services contain business logic. Models define data. Never put business logic in routers.
- **All community features require auth**: Posting recruitment, professions, LFG, trade, and voting all require an authenticated email account. Features requiring character ownership (guild officer actions, profession listings) additionally require Battle.net linking.

## Git Workflow

- Branch from `main` for each feature: `feature/CTBC-E{epic}-S{story}-{description}`
- Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:` prefixes
- All PRs must pass CI (full quality chain) before merge
- Never commit directly to `main`
