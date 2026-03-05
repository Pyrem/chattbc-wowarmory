# chattbc.gg

TBC-era World of Warcraft armory and community platform with an AI-powered chatbot.

## Project Structure

```
chattbc-wowarmory/
  frontend/       # Next.js 14+, TypeScript, Tailwind, shadcn/ui
  backend/        # Python 3.12+, FastAPI, SQLAlchemy, Alembic
    app/
      routers/    # HTTP route handlers
      models/     # SQLAlchemy ORM models
      schemas/    # Pydantic request/response schemas
      services/   # Business logic layer
    tests/
      unit/
      integration/
  infra/
    cdk/          # AWS CDK stacks
    lambdas/      # Bedrock Agent action group handlers
  e2e/            # Playwright E2E tests
  shared/
    tbc_data/     # Static TBC game data (attunements, items, etc.)
  rules/          # ast-grep rules
  .semgrep/       # Semgrep custom rules
  scripts/        # Utility scripts
  docs/           # Architecture, conventions, data models, stories
```

## Quick Start

```bash
# Start local Postgres + Redis
docker-compose up -d

# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

## Code Quality

```bash
make quality    # Full chain: lint -> typecheck -> ast-grep -> semgrep -> tests
make lint       # Ruff + ESLint + Prettier
make typecheck  # mypy --strict
make scan       # ast-grep + Semgrep
make test       # pytest + Vitest
```

## Database

```bash
make migrate              # Run migrations (alembic upgrade head)
make migration            # Generate new migration
```
