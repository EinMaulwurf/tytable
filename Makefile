.PHONY: install lint format format-docs typecheck test test-images docs docs-watch clean

install:
	uv sync --all-extras

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

format-docs:
	typstyle --line-width 120 --inplace docs/*.typ

typecheck:
	uv run mypy

test:
	uv run pytest --cov=tytable --cov-report=term-missing -m "not images"

test-images:
	uv run pytest -m "images"

docs: format-docs
	MPLCONFIGDIR=$(CURDIR)/docs/build/.mplconfig uv run python docs/build_examples.py
	typst compile docs/main.typ docs/tytable-docs.pdf

docs-watch: format-docs
	MPLCONFIGDIR=$(CURDIR)/docs/build/.mplconfig uv run python docs/build_examples.py
	typst watch docs/main.typ docs/tytable-docs.pdf

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf docs/build docs/tytable-docs.pdf
	find . -type d -name tytable_assets -exec rm -rf {} +
