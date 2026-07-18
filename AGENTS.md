# AGENTS.md

## Project identity

**Package**: `tytable` — source: `src/tytable/`

A lightweight Python package for creating typst tables from (polars) dataframes. Inspired by the tinytable R package.

**Version 2 direction:** The current v2 work aims to reduce complexity in both the public API and
the internals while preserving a flexible, modern user experience.

## Commands

```bash
make install      # uv sync --all-extras
make lint         # ruff check src tests
make format       # ruff format src tests
make typecheck    # mypy
make test         # pytest -m "not images" (excludes images tests)
make test-images  # pytest -m "images" (requires matplotlib)
```

Pre-commit order: `lint` → `typecheck` → `test`.

## Release workflow

**Semantic-versioning rule:** Do not include breaking changes to the documented public API in
minor or patch releases. Preserve compatibility throughout the 1.x series and defer any such
changes to 2.0.0 (recording them under `Breaking` in `CHANGELOG.md`).

1. Keep notable user-facing changes under `Unreleased` in `CHANGELOG.md`. To release, rename that
   section to `[X.Y.Z] - YYYY-MM-DD`, add a new empty `Unreleased` section, update the comparison
   links at the bottom, run the checks above, commit, and push `main`.
2. Tag that commit and push the tag:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

3. Verify the `Release` GitHub Actions run. CI builds and validates the wheel/sdist, creates the
   GitHub release from the matching changelog entry, attaches the artifacts, and publishes to PyPI
   through trusted publishing; do not upload packages manually. The workflow fails if the matching
   changelog entry is missing, duplicated, or empty.

## Tooling quirks

- **ruff**: line-length 100, double-quotes, selects E/F/I/UP/B/SIM/C4; E501 ignored
- **mypy**: non-strict, ignores missing imports, only checks `src/tytable` (not tests)
- **Coverage**: 80% branch minimum

## Testing

- Custom snapshot helper at `tests/helpers.py:assert_snapshot`. Set `SNAPSHOT_UPDATE=1` to regenerate.
- `conftest.py` monkeypatches `_new_image_id` for deterministic image tests.
- Performance gate: `test_perf.py` asserts a 120×30 table renders under 0.3 s.
- Pytest markers: `typst`, `html`, `images`. Default `make test` skips `images` (needs the `images` extra).

## Architecture

```text
tt(df, ...)               # _tytable.py — factory + TyTable class
  .style() / .fmt() / ... # record directives (StyleDirective, FormatDirective, …)
  .render() / .save()     # resolve pipeline → render

build()                   # _resolve.py — resolve directives → BuiltTable
  → TypstRenderer         # _render_typst.py
  → HtmlRenderer          # _render_html.py
  → AsciiRenderer         # _render_ascii.py
```

Styling, formatting, grouping, and plotting are recorded as **intent** and replayed in a fixed
order at render time. Public row indices always refer to stable, 0-based source DataFrame rows;
inserted group rows and headers are selected by explicit semantic names.

### Key modules

| File               | Role                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `_tytable.py`      | Public API: `TyTable` class, `tt()` factory                                                       |
| `_directives.py`   | Dataclasses: `StyleDirective`, `FormatDirective`, `PlotDirective`, `Note`, `RowGroup`, `ColGroup` |
| `_resolve.py`      | `build()` pipeline and `BuiltTable` output dataclass                                              |
| `_styling.py`      | Style validation, style-grid construction                                                         |
| `_format.py`       | Numeric formatting, replace, escape, fn transforms                                                |
| `_groups.py`       | Row/column group registration and merging                                                         |
| `_themes.py`       | Resolution of the replaceable base appearances (`default`, `plain`, `striped`, `grid`)            |
| `_render_typst.py` | Typst output (primary output format)                                                              |
| `_render_html.py`  | HTML preview (Jupyter `_repr_html_`)                                                              |
| `_render_ascii.py` | ASCII `__repr__`                                                                                  |
| `_images.py`       | Plot/image embedding (requires `images` extra)                                                    |

`docs/` contains several small, standalone python scripts with examples and a `.typ` file which is compiled to a standalone documentation PDF on every push and release.

## Commit style

Conventional commits: `type(scope): description`. Types: `feat`, `fix`, `docs`, `test`, `ci`, `build`, `refactor`. Scope optional. Keep descriptions imperative and lowercase. Examples from history: `refactor: make themes replaceable base appearances`, `fix: resolve all 20 mypy type-checking errors`, `docs: add docstrings to all public API`.

- All source modules start with `_` (private). Public API is only what `__init__.py` exports.
- **Semantic row selection**: `i=0` is the first source-data row, even after grouping inserts
  rows. Use `i="header"`, `i="groupi"`, and `i="groupj"` for structural rows; negative public
  row indices are not supported.
- Column selection by **name** (`j="Score"`) preferred over integer position.
- Method chaining: `.style()`, `.fmt()`, `.group()`, the `.theme_*()` methods, and layout methods
  such as `.rotate()` return `self`. `.render()` / `.save()` are terminal.
- Internal imports use `from tytable._resolve import build`, not relative paths (most files already use this pattern).
