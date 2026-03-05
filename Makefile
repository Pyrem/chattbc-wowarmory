.PHONY: quality lint typecheck scan test lint-py lint-ts typecheck-py scan-ast scan-semgrep test-py test-ts

# Full quality chain — run before every commit
quality: lint typecheck scan test

# Linting
lint: lint-py lint-ts

lint-py:
	cd backend && ruff check --fix . && ruff format .

lint-ts:
	cd frontend && npx eslint --fix . && npx prettier --write .

# Type checking
typecheck: typecheck-py

typecheck-py:
	cd backend && mypy --strict app/

# Static analysis
scan: scan-ast scan-semgrep

scan-ast:
	ast-grep scan

scan-semgrep:
	semgrep --config=.semgrep/ --quiet

# Tests
test: test-py test-ts

test-py:
	cd backend && pytest

test-ts:
	cd frontend && npx vitest run

# Local dev environment
up:
	docker-compose up -d

down:
	docker-compose down

# Database migrations
migrate:
	cd backend && alembic upgrade head

migration:
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"
