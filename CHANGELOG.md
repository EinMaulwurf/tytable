# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-07-17

### Features

- Add `.style(where=...)` and `.fmt(where=...)` for cell-level conditional operations with
  multi-column Polars expressions, while preserving the existing row/column cross-product when
  omitted.

### Docs / CI

- Support Typst 0.11.0 or newer, compile generated tables against Typst 0.11.0, 0.14.2,
  and 0.15.0 in CI, and build published documentation with Typst 0.15.0. Compiler
  diagnostics are included in test failures.

## [1.0.0] - 2026-07-16

### Breaking

- Rename the public `TinyTable` class to `TyTable`; replace imports such as
  `from tytable import TinyTable` with `from tytable import TyTable`. The `tt()`
  factory remains unchanged.
- Replace delimiter-based `.group(j="_")` calls with the explicit
  `.group(delimiter="_")` parameter; `j=` now accepts column-group mappings only.
- Right-align columns with Polars numeric dtypes, including their headers, by default.
  Text and other non-numeric columns remain left-aligned, and explicit alignment styles
  retain precedence.
- Remove the `theme=` constructor option. Tables retain the implicit default
  booktab styling; apply built-ins through typed chainable methods such as
  `.theme_striped()`, `.theme_grid()`, `.theme_rotate()`, and `.theme_resize()`.
  `.theme()` now accepts custom callables only.
- Make `.theme_empty()` the explicit, order-sensitive reset for starting from
  an unstyled table. It clears prior theme/style/format intent while preserving
  constructor-level figure and layout options.

### Features

- Add `.theme_multipage(repeat_headers=True)` for breakable Typst tables with
  optional repeated header rows.
- Add `num_fmt="scientific"` to `.fmt()` with native mathematical notation in
  Typst and HTML output.
- Add `.fmt(linebreak=...)` for safe backend-native multiline cells and
  `.fmt(math=True)` for Typst equations.

### Fixes

- Allow `.images()` to embed existing files without installing plotting dependencies.
- Apply `.plot()` pixel dimensions consistently to both Matplotlib and plotnine
  output.
- Render ASCII previews as native plain text instead of leaking HTML entities and
  footnote tags, include captions and notes, and align/truncate Unicode content by
  terminal display width.

### Docs / CI

- Remove redundant development dependencies and enforce the configured branch-coverage gate in
  the default test and CI commands.
- Test on Python 3.14 and advertise support for Python 3.10 through 3.14.
- Expose documentation, changelog, and issue-tracker links in the PyPI project metadata.
- Build and attach the documentation PDF directly in the release workflow, and restrict release
  assets to distributions and the PDF.
- Add an advanced `TyTable` programming guide, a polished table showcase, and a task-oriented API
  reference with selector and method summaries.
- Document installation from PyPI in the README and PDF guide.
- Add a Mizani integration example for scales-style currency and percentage labels.

## [0.6.0] - 2026-07-14

### Fixes

- Reject unknown Typst theme options with a clear error instead of silently accepting typos.
- Limit regex selector length to guard against excessively large patterns.
- Clean up temporary portable plot files even when plot generation fails.
- Preserve user style precedence over styles applied by themes at render time.

### Performance

- Cache repeated Typst text escaping, color conversion, and style signature generation.
- Precompute active style properties when building the cell style grid.

### Internal

- Split the build pipeline into explicit phases and introduced a shared renderer interface.
- Consolidated style markup translation and column-group span resolution across renderers.
- Separated plot and image directives and simplified complex formatting, styling, and rendering
  methods.
- Expanded regression coverage for formatting, styling, grouping, colors, images, selectors, and
  utility functions.

### Docs / CI

- Documented the theme registry and exceptions raised by the public API.
- Added tag-triggered PyPI publishing.
- Forced Matplotlib's non-interactive `Agg` backend for reliable image tests on headless runners.

[Full changelog](https://github.com/EinMaulwurf/tytable/compare/0.5.0...v0.6.0)

## [0.5.0] - 2026-07-14

### Breaking

- License switched from MIT to **GPL-3.0-only**. Downstream users who redistribute or merge
  this code into larger works are now bound by the GPL-3.0-only terms; permissive re-use is no
  longer permitted. Update `LICENSE`/`NOTICE` files accordingly.

### Features

- `figure` and `label` options exposed on the table so rendered output can be wrapped in a
  `#figure` with a caption and a cross-referenceable label.
- Explicit figure alignment values are now preserved instead of being overridden by defaults.

### Fixes

- Six critical security and correctness bugs resolved:
  - `apply_formats` no longer applies directives to wrong rows on falsy/fallback inputs.
  - Replaced the `startswith('<img')` escape bypass with explicit image-cell tracking.
  - Unsafe characters in unrecognized color values passed to Typst are now rejected.
  - Matplotlib import deferred to render time, eliminating a ~310 ms startup penalty.
  - Stopped double-escaping HTML column names (pre-escape now skipped for HTML/ASCII).
  - CSS style property values validated to prevent HTML/CSS injection.
- Escaped backticks and tildes in Typst text; made escape helpers type-safe; validated
  `set_name` name types; hardened Typst styles and width validation.
- Applied formatting to column headers; preserved frozen notes when assigning markers; kept
  table rendering idempotent.
- Rotated content now respects `align`/`alignv`: the `rotate` show rule is wrapped in
  `align(...)` so alignment applies inside the rotated box.
- Internal refactor: parameterized directive list types.

### Docs / CI

- Added a table of contents after the title page, plus a short commit hash and build date stamp
  on the title page (via `build/meta.typ` generated by `build_examples.py`).
- Removed `pip install` from README and docs (package not on PyPI yet) and shortened the install
  sub-heading.
- Tightened `SOURCE`/`RESULT` tag spacing in examples.

## [0.4.0] - 2026-07-13

### Breaking

- Column selectors are now exact-match by default. String `j=` selectors no longer silently
  fall back to `re.search` on a miss—they raise `ValueError` instead, so typos in column names
  surface immediately. Pass `regex=True` to `.style()`, `.fmt()`, `.plot()`, `.images()`, or
  `.set_name()` to opt back into regex matching (works for list selectors too, where each
  element is treated as a pattern).

### Features

- `rotate` style property for per-cell content rotation in `.style()`.
- Normalize column `width` lists whose entries sum past `1`, and validate width entries up front
  (clearer errors instead of odd rendering).

### Docs / CI

- Slimmed README; docs PDF deployed to GitHub Pages.
- Bumped `actions/checkout` to v5.

## [0.3.1] - 2026-07-13

### Fixes

- Run `ruff format` on `src/` and `tests/` to satisfy the `ruff format --check` CI gate (no code
  changes).

## [0.3.0] - 2026-07-13

### Features

- List-of-str column selectors (`j=["A", "B"]`) plus data-driven row selectors: `polars.Expr`,
  boolean `Series`, or `callable(row) -> bool`.
- `.set_name()` for display-only column renaming (names Polars rejects are now allowed).
- Per-column `align`/`alignv` strings in `.style()`.
- Style the caption and footnotes via `i="caption"` / `i="notes"`.
- `resize` theme to scale tables to fit the page.

### Fixes

- Support 4- and 8-digit hex colors (`#RGBA`, `#RRGGBBAA`) in `.style()`.
- Widen `replace` type (`dict | str | bool | None`) and make `width` covariant
  (`Sequence[...]`) so `list[int]` is accepted.

## [0.2.0] - 2026-07-12

### What's new

- New list-of-str selectors and data-driven row selectors.
- Style captions and footnotes via `i="caption"` / `i="notes"`.
- Resize theme to scale tables to fit the page.
- String sentinel keys in `fmt` replace dict (`"null"`, `"nan"`, `"inf"`, `"-inf"`).
- Resolve all mypy type-checking errors.
- Lint/test CI workflow and pre-commit hooks.
- Version now derived from git tags via hatch-vcs.
- Miscellaneous docs improvements.

## [0.1.1] - 2026-07-10

No release notes were provided for this release.

## [0.1.0] - 2026-07-10

No release notes were provided for this release.

[Unreleased]: https://github.com/EinMaulwurf/tytable/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/EinMaulwurf/tytable/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/EinMaulwurf/tytable/compare/v0.6.0...v1.0.0
[0.6.0]: https://github.com/EinMaulwurf/tytable/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/EinMaulwurf/tytable/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/EinMaulwurf/tytable/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/EinMaulwurf/tytable/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/EinMaulwurf/tytable/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/EinMaulwurf/tytable/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/EinMaulwurf/tytable/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/EinMaulwurf/tytable/releases/tag/v0.1.0
