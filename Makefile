.PHONY: bootstrap install dev-backend dev-frontend dev \
        test-backend test-frontend test-e2e test \
        lint-backend lint-frontend lint \
        typecheck-backend typecheck-frontend typecheck \
        format migrate clean

# ─── Bootstrap ────────────────────────────────────────────────────────────────

bootstrap:
	cd apps/api && uv sync --extra dev
	cd apps/web && pnpm install

install: bootstrap

# ─── Dev servers ──────────────────────────────────────────────────────────────

dev-backend:
	cd apps/api && uv run uvicorn wheel_vocabulary.api.main:create_app --factory --reload

dev-frontend:
	cd apps/web && pnpm run dev

dev:
	$(MAKE) dev-backend & $(MAKE) dev-frontend

# ─── Tests ────────────────────────────────────────────────────────────────────

test-backend:
	cd apps/api && uv run pytest

test-frontend:
	cd apps/web && pnpm run test

test-e2e:
	cd apps/web && pnpm exec playwright test

test: test-backend test-frontend test-e2e

# ─── Lint ─────────────────────────────────────────────────────────────────────

lint-backend:
	cd apps/api && uv run ruff check .

lint-frontend:
	cd apps/web && pnpm run lint

lint: lint-backend lint-frontend

# ─── Type-check ───────────────────────────────────────────────────────────────

typecheck-backend:
	cd apps/api && uv run mypy src/wheel_vocabulary

typecheck-frontend:
	cd apps/web && pnpm run typecheck

typecheck: typecheck-backend typecheck-frontend

# ─── Format ───────────────────────────────────────────────────────────────────

format:
	cd apps/api && uv run ruff format .

# ─── Database ─────────────────────────────────────────────────────────────────

migrate:
	cd apps/api && uv run alembic upgrade head

# ─── Clean ────────────────────────────────────────────────────────────────────

clean:
	rm -rf apps/api/.venv
	rm -rf apps/web/node_modules
	rm -rf apps/api/.pytest_cache apps/api/.mypy_cache apps/api/.ruff_cache
	rm -rf apps/api/htmlcov apps/api/.coverage apps/api/coverage.xml
	rm -rf apps/web/dist apps/web/coverage
	find apps/api -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
