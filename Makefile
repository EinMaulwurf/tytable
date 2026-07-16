.PHONY: install lint format typecheck test test-images docs docs-watch clean

install:
	uv sync --all-extras

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run mypy

test:
	uv run pytest -m "not images"

test-images:
	uv run pytest -m "images"

docs:
	MPLCONFIGDIR=$(CURDIR)/docs/build/.mplconfig uv run python docs/build_examples.py
	typst compile docs/main.typ docs/tytable-docs.pdf

docs-watch:
	MPLCONFIGDIR=$(CURDIR)/docs/build/.mplconfig uv run python docs/build_examples.py
	typst watch docs/main.typ docs/tytable-docs.pdf

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf docs/build docs/tytable-docs.pdf
	find . -type d -name tytable_assets -exec rm -rf {} +
