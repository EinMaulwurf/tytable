# TODO

## Feature: list-of-str column selectors ✅

`.style()` / `.fmt()` / `.group()` accept `j=["ColA", "ColB"]` at runtime
(`resolve_j` in `_indices.py` handles `list[str]`), but their public type
annotations only allow `list[int]`. Widen the `j` (and `i`) annotations to
  `int | str | Sequence[int | str] | None` so callers like
  `.style(j=["Revenue", "Cost", "Growth"], align="r")` type-check cleanly.

---

# TODO: Missing features (from tinytable comparison)

> **Reference:** the R original lives at `/home/debian/git/tinytable/` (source in
> `R/`). When implementing any item below, read the corresponding tinytable file
> for behaviour and edge cases — the goal is feature parity within tytable's
> Typst-first scope, not a 1:1 port. See `tinytable/CLAUDE.md` for the R
> architecture and `tinytables_python_guide/02_scope_and_decisions.md` for what
> is deliberately out of scope (LaTeX/Word/PDF/Markdown/Tabulator/Quarto/ANSI
> are intentionally excluded).

## High value, in scope, low effort

### Feature: data-driven row selectors ✅

No way to select rows by value. tinytable accepts NSE expressions
(`style_tt(i = mpg > 20, …)`) and boolean matrices. Add a Pythonic form: accept
a Polars expression, a boolean `pl.Series`, or a `callable(row) -> bool` for
`i` (e.g. `.style(i=pl.col("Score") > 80, …)`). See
`/home/debian/git/tinytable/R/style_tt.R` (NSE `i` handling) and `R/nse.R`.

### Feature: `num_fmt="scientific"`

Add alongside `decimal`/`significant` in `_format.py`
(`_fmt_numeric_scientific` → `f"{val:.{digits}e}"`). See
`/home/debian/git/tinytable/R/format_vector_numeric.R`.

## Medium value

### Feature: column hiding / subset

No way to drop a column at table level without filtering the frame first (which
loses the original index → column mapping used by selectors). Add a `.hide(j=…)`
or `tt(cols=…)` selector. typ-tables calls this `cols_hide`. See
`/home/debian/git/tinytable/R/subset.R`.

### Feature: `linebreak` marker replacement

tinytable replaces a placeholder (e.g. `"\n"`) with the backend's line break
(`\ ` in Typst, `<br>` in HTML). With `escape=True` by default there is currently
no clean way to get a multi-line cell. Add a small `.fmt(linebreak=…)`. See
`/home/debian/git/tinytable/R/format_vector_misc.R`
(`format_vector_linebreak`).

### Feature: combine two tables (`rbind`)

tinytable has `rbind2()` to stack two tables. Add a `.append()` or classmethod.
Low priority — documenting "concat frames first" may suffice. See
`/home/debian/git/tinytable/R/rbind2.R`.

### Feature: width auto-normalization

`_columns_spec` (`_render_typst.py`) multiplies each list element by 100
directly, so `width=[3, 1]` yields `300%, 100%` instead of `75%, 25%`. tinytable
normalizes a width vector to sum=1. Add normalization so fractional vectors sum
to 100%. See `/home/debian/git/tinytable/R/tt.R` (width handling, lines ~241).

## Nice-to-have (deferred in the guide)

### Feature: `set_option()` / config mechanism

The guide parks this ("can come later"). A thin global-defaults mechanism for
`escape` / `digits` / `theme` / `width`. See tinytable's `getOption(
"tinytable_*" )` cascade — `/home/debian/git/tinytable/R/package.R` and the
`get_option` calls throughout `R/tt.R`, `R/format_tt.R`, `R/style_tt.R`.

### Feature: `quarto_compat` flag

Drop the `#figure(...)` wrapper and do `#block` → `block` so the fragment can be
embedded in Quarto-Typst output. Guide §6.9 defers this. See
`/home/debian/git/tinytable/R/typst_finalize.R`.

### Feature: `math` mode

Wrap cell values in Typst math (`$…$`) for equations. Small, typst-natural add.
See `/home/debian/git/tinytable/R/format_vector_misc.R`
(`format_vector_math`).

## Known correctness edge cases (not features)

- `figure=False` + `multipage` emits a possibly-invalid `#set page(breakable:
  …)` (`_render_typst.py:118-120`). No test exercises this combination.
- `fmt(i="header")` is silently dropped — `data_body` contains only body rows,
  so format directives targeting the header never apply. Low priority (format
  column names in polars, or via `colnames_override`).

---

# TODO: Pre-existing mypy issues

These errors existed before the July 2026 type annotation additions and are not
introduced by those changes. They should be addressed separately.

## _format.py (2 errors)

- `_fmt_numeric_decimal` / `_fmt_numeric_significant` — `val: object` is passed
  to `float()`. Callers guard with `_is_numeric_typed()`, so it's safe at runtime
  but mypy can't narrow through the custom guard.

## _images.py (1 error)

- `execute_plots` line 193 — `assets_dir` variable is reassigned from
  `str | None` to `Path`. Use a separate variable.

## _render_html.py (3 errors)

- `HtmlRenderer.render` lines 173, 176, 177 — row iteration over
  `built.data_body` hits list invariance and variable type reassignment issues
  with the col-groups and enumeration.

## _render_typst.py (1 error)

- `TypstRenderer.render` line 171 — same list invariance issue as
  `_render_html.py` when iterating `built.data_body`.

## _resolve.py (4 errors)

- `_insert_footnote_markers` line 71 — `i_vals` from `resolve_i` may be `None`,
  iterated without a guard.
- `build` lines 109, 146, 167 — variable type reassignments and
  `list[list]` / `list[list[object]]` mismatch at call sites.

## _styling.py (3 errors)

- `_validate_style` lines 60, 65 — loop variable `val` reassigned across
  different types.
- `build_style_grid` line 90 — `i_vals` from `resolve_i` may be `None`,
  iterated without a guard.

## _tinytable.py (6 errors)

- `tt()` line 35 — `data: object` passed to `TinyTable.__init__` which expects
  `DataFrame`.
- `_normalize_notes` line 57 — `raw: object` is iterated.
- `_assign_markers` lines 82, 84 — `object.__setattr__` doesn't return a value;
  the `note =` assignment is a no-op.
