.PHONY: lint format typecheck test test-cov check

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/ && uv run ruff check --fix src/ tests/

typecheck:
	uv run mypy src/voiceforge/

test:
	uv run pytest -m "not gpu"

test-cov:
	uv run pytest -m "not gpu" --cov --cov-report=term-missing

check: lint typecheck test
