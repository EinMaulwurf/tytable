# AGENTS.md

## Project identity

**Package**: `tytable` — source: `src/tytable/`

A lightweight Python package for creating typst tables from (polars) dataframes. Inspired by the tinytable R package.

## Commands

```bash
make install      # uv sync --all-extras
make lint         # ruff check src tests
make format       # ruff format src tests
make typecheck    # mypy
make test         # pytest -m "not images" (excludes images tests)
make test-images  # pytest -m "images" (requires matplotlib/numpy)
```

Pre-commit order: `lint` → `typecheck` → `test`.

## Tooling quirks

- **ruff**: line-length 100, double-quotes, selects E/F/I/UP/B/SIM/C4; E501 ignored
- **mypy**: non-strict, ignores missing imports, only checks `src/tytable` (not tests)
- **Coverage**: 80% branch minimum

## Testing

- Custom snapshot helper at `tests/helpers.py:assert_snapshot`. Set `SNAPSHOT_UPDATE=1` to regenerate.
- `conftest.py` monkeypatches `_new_image_id` for deterministic image tests.
- Performance gate: `test_perf.py` asserts a 120×30 table renders under 0.3 s.
- Pytest markers: `typst`, `html`, `images`. Default `make test` skips `images` (needs the `images` extra).
- The `pytest-snapshot` dep is in `pyproject.toml` but **not** the active snapshot mechanism — `tests/helpers.py` handles snapshots.

## Architecture

```text
tt(df, ...)               # _tytable.py — factory + TinyTable class
  .style() / .fmt() / ... # record directives (StyleDirective, FormatDirective, …)
  .render() / .save()     # resolve pipeline → render

build()                   # _resolve.py — resolve directives → BuiltTable
  → TypstRenderer         # _render_typst.py
  → HtmlRenderer          # _render_html.py
  → AsciiRenderer         # _render_ascii.py
```

Styling, formatting, grouping, and plotting are recorded as **intent** and replayed in a fixed order at render time. Row indices always refer to the final, visible table.

### Key modules

| File               | Role                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `_tytable.py`      | Public API: `TinyTable` class, `tt()` factory                                                     |
| `_directives.py`   | Dataclasses: `StyleDirective`, `FormatDirective`, `PlotDirective`, `Note`, `RowGroup`, `ColGroup` |
| `_resolve.py`      | `build()` pipeline and `BuiltTable` output dataclass                                              |
| `_styling.py`      | Style validation, style-grid construction                                                         |
| `_format.py`       | Numeric formatting, replace, escape, fn transforms                                                |
| `_groups.py`       | Row/column group registration and merging                                                         |
| `_themes.py`       | Theme registry (`default`, `striped`, `grid`, `empty`, `rotate`)                                  |
| `_render_typst.py` | Typst output (primary output format)                                                              |
| `_render_html.py`  | HTML preview (Jupyter `_repr_html_`)                                                              |
| `_render_ascii.py` | ASCII `__repr__`                                                                                  |
| `_images.py`       | Plot/image embedding (requires `images` extra)                                                    |

## Conventions

- All source modules start with `_` (private). Public API is only what `__init__.py` exports.
- **0-based row indexing**: `i=0` is first data row; `i="header"` for column-name row; negative ints for column-group header rows.
- Column selection by **name** (`j="Score"`) preferred over integer position.
- Method chaining: `.style()`, `.fmt()`, `.group()`, `.theme()` return `self`. `.render()` / `.save()` are terminal.
- Internal imports use `from tytable._resolve import build`, not relative paths (most files already use this pattern).
