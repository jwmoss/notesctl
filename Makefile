.PHONY: check test build

check:
	uv lock --check --no-config
	uv sync --locked --all-extras --no-config
	uv run --locked --no-config ruff check src/ scripts/
	uv run --locked --no-config ruff format --check src/ scripts/
	uv run --locked --no-config ty check
	uv build --no-config

test:
	uv run --locked --no-config python scripts/live-e2e.py

build:
	uv build --no-config
