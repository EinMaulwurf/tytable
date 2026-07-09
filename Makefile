.PHONY: install lint format typecheck test test-images clean

install:
	uv sync --all-extras

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy

test:
	pytest -m "not images"

test-images:
	pytest -m "images"

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name tinytable_assets -exec rm -rf {} +
