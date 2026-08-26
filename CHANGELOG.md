# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Features

- Add a `scale` option to the `number`, `currency`, and `unit` formatters. The existing `percent` formatter continues to use `scale=100` by default.
- Add flexible decimal places, named rounding modes, negative-zero cleanup, special-value labels, and five notation modes to semantic numeric formatters.
- Add custom compact labels and promote compact or SI values when rounding crosses the next prefix boundary.
- Let `currency()` forward numeric options, control symbol position, and use known currency digits when `digits=None`.
- Add IEC binary prefixes to `unit()`, human-readable output to `duration()`, and timezone conversion to `date()`.

### Fixes

- Reject unsupported `.fmt(replace=...)` and `fn_values` types immediately instead of silently ignoring them or exposing incidental errors.
- Require callable row selectors to return genuine Boolean values for every source row.
- Save ASCII output to `.txt` files. Reject other unsupported `.save()` suffixes instead of writing Typst source to files such as PDF files.
- Accept one backend name or a sequence in directive `output` filters. Validate and normalize the filter when the directive is registered.
- Validate constructor row height, media height, and Typst layout options when their public methods are called.
- Require genuine Boolean values for constructor, formatting, and styling Boolean options.
- Reject malformed note collections, unsupported entries, unknown `NoteDict` keys, and invalid note field types instead of silently coercing or ignoring them.
- Validate plot data, limits, and color along with static-image path collections when media directives are registered.
- Advertise the existing path-like object support in `.save()` annotations for both the output and asset paths.
- Include the existing public `__version__` attribute in the package's declared exports.
- Use contextual `TypeError` failures for invalid formatter option types and consistent `ValueError` failures for out-of-range public positions.

### Deprecated

- Version 4.0 will remove `.fmt(digits=..., num_fmt=...)`. Version 3.x continues to support it. Semantic formatters from `tytable.formatters` replace it in new code.
- Version 4.0 will rename `.plot(fun=...)` to `.plot(fn=...)`. It will also validate callbacks for `.fmt()`, `.plot()`, and `.finalize()` when each method is called.

## [3.0.1] - 2026-08-22

### Fixes

- Restore the documented 0.3-second performance-test budget so normal CI runner variance does not fail an otherwise successful test matrix.

### Documentation

- Correct the authoritative selector table after a missing cell shifted later entries into the wrong columns, and rebalance its column widths.
- Give each deployed Pages PDF a revision-specific URL so browsers do not display a stale embedded manual after an update.

## [3.0.0] - 2026-08-21

Version 3 makes tytable more DataFrame-native: formatting operates on typed source values, selectors compose across source schemas and structural groups, and display-only transformations preserve stable source identities.

### Breaking

- Replace the `regex=True` argument on `.style()`, `.fmt()`, `.plot()`, `.images()`, and `.set_name()`, and the `regex` key in targeted `NoteDict` entries, with the explicit `regex(pattern)` column selector. Import it with `from tytable.selectors import regex`, then change calls such as `j=r"^Q", regex=True` to `j=regex(r"^Q")`; mixed selections can use forms such as `j=["Total", regex(r"^Q")]`. The selector retains Python `re.search` semantics, the 500-character limit, and errors for invalid patterns or patterns that match no source columns.
- In 3.0, make `.fmt(fn=...)` receive original typed DataFrame values by default. Pass `fn_values="display"` when a callback should consume current display strings or the result of `digits`. Earlier 3.0 development builds briefly exposed a separate `formatter` argument; pass semantic formatters through `fn` instead.

### Features

- Add `rowgroup(label=...)` for selecting the source-data rows belonging to exact row-group labels, and `colgroup(label=..., level=...)` for selecting the source columns belonging to exact labels at stable column-group levels.
- Add composable `regex(pattern)` selectors anywhere `j` selects source columns, including display projection and column-group specifications.
- Add `groupi(label=...)` for selecting every row-group separator with an exact registered label, while `groupi()` selects every row-group separator.
- Add `groupj(level=...)` for styling one stable nested column-group header level, with level zero assigned to the first-created innermost level, and make `j` select the spanning group-header cell covering each chosen source column.
- Add `.show_columns()` for display-only column projection while keeping omitted source columns available to selectors and conditional formatting.
- Accept Polars column selectors such as `cs.numeric()`, `cs.string()`, `cs.starts_with(...)`, and `cs.by_dtype(...)` anywhere `j` selects columns.
- Add reusable selectors for regular expressions and semantic row and column groups, available as direct imports from `tytable.selectors`.
- Add reusable number, currency, percentage, date, duration, and unit formatters with German and English separator presets, available as direct imports from `tytable.formatters`.
- Add `.clone()` for deriving independently configurable variants from a shared table definition.
- Add `.compile()` for direct PDF, PNG, and SVG output through an installed Typst CLI.

### Fixes

- Reject row groups that reuse a source-row position across chained `.group(i=...)` calls.
- Reject empty and whitespace-only column-group labels so every registered label is selectable with `colgroup(...)`.
- Render HTML vertical cell alignment with `vertical-align` instead of combining it with `text-align`.
- Preserve outer HTML borders styled on cells covered by a column or row span.
- Render `colspan` and `rowspan` styles on HTML column-name header cells.
- Reject negative `fontsize` and `indent` style values.
- Emit HTML captions before column-width declarations, as required by HTML table element ordering.
- Render zero-column tables as an explicit empty-table message in ASCII output.

### Documentation

- Add a rendered guide to semantic number, currency, percentage, date, duration, and unit formatters while keeping quick references concise, including the distinction between callbacks and formatter factories.

## [2.2.0] - 2026-08-11

### Features

- Add portable per-cell padding with uniform, vertical/horizontal, or per-side values.
- Add solid, dashed, dotted, dash-dotted, and removable cell borders with last-writer-wins resolution on shared physical edges.
- Add explicit Typst `column_gutter` and `row_gutter` controls while preserving the legacy grouped-table `gutter` behavior.

### Fixes

- Remove the inert `line_trim` style option, which was accepted but never affected any renderer.

### Performance

- Prepare replacement mappings and row-group membership once per render phase instead of rebuilding them inside cell loops.

### Documentation

- Format Typst documentation sources with Typstyle before local and CI builds.

## [2.1.0] - 2026-07-20

### Features

- Give targeted notes the same `where` and `regex` cell-selection semantics as formatting and styling directives.
- Let `.fmt(fn=..., fn_values="typed")` pass original DataFrame values to custom formatting callbacks while preserving display-string callbacks by default.

## [2.0.1] - 2026-07-19

### Fixes

- Decode embedded media through Typst's version-appropriate API and require Typst 0.11.1 or newer because Typst 0.11.0 does not expose in-memory image decoding.

## [2.0.0] - 2026-07-19

Version 2 makes selectors, themes, and media handling more predictable while removing redundant ways to configure the same behavior.

### Features

- Accept `range` and other selector sequences for row and column selectors while continuing to reject arbitrary iterables whose contents or order may not be stable across deferred renders.

### Breaking

- Make `default`, `plain`, `striped`, and `grid` replaceable base appearances which are applied before explicit styles regardless of call order. Replace destructive `.theme_empty()` with `.theme_plain()`, remove `.theme(fn)` and the public `THEMES` registry, and rename the independent layout operations to `.rotate()`, `.resize()`, and `.multipage()`.
- Make omitted row selectors target genuine source-data rows, add `i="data"`, and reserve `i="all"` for the complete grid. Non-negative integers now always address stable 0-based source DataFrame rows; remove negative indices and the ambiguous `i="body"` / `i="~groupi"` names. Resolved row and column selections are deduplicated into canonical displayed row-major order, including targeted notes and media cardinality.
- Reject structural row kinds that a content operation cannot represent instead of silently ignoring them. Styling still supports the whole grid; formatting and targeted notes support data, row-group, and column-name rows; plots and images support data and row-group rows.
- Resolve every `j` selector against the original DataFrame column names. Display labels assigned by `.set_name()` are presentation-only, so renaming headers cannot change which columns later directives select and duplicate or empty display labels remain unambiguous.
- Make `.render()` filesystem-side-effect-free by embedding generated plots, and make `.save()` independently materialize them in a table-specific `<stem>_assets/` directory by default.
- Make `.save()` copy static `.images()` inputs into its asset directory by default. Add explicit `copy`, `reference`, and `embed` policies so saved tables can be packaged, externally managed, or self-contained, and make `assets=` cover all externalized media.
- Remove the inert `rownames` and constructor-level `digits` parameters from `tt()` and `TyTable`; configure numeric formatting with `.fmt(digits=...)`.
- Remove `colnames_override` from `tt()` and `TyTable`; rename display headers with `.set_name(name={"source_name": "Display name"})` instead.
- Remove the constructor-level `finalize` shortcut from `tt()`; register output callbacks with the chainable `.finalize(fn)` method.
- Make the plotting callback in `.plot(fun=...)` and the image sequence in `.images(paths=...)` required keyword arguments instead of optional parameters rejected at runtime.

### Documentation

- Carry the three-part tutorial, advanced-guides, and reference organization forward with the version 2 API, selector semantics, themes, media policies, and rendering contracts.

## [1.3.0] - 2026-07-17

### Features

- Export `NoteDict` so note dictionary keys and selectors are discoverable to type checkers and
  IDEs.

### Fixes

- Accept narrow and read-only collection types in public annotations, including `list[int]`
  column groups, `list[str]` row groups, mixed column selectors, and integer plot limits.
- Require `.images(paths=...)` and explicit `.plot(data=...)` inputs to contain exactly one
  item per resolved media cell.
- Validate `.fmt()` numeric options and callback contracts instead of silently accepting unknown
  numeric formats or exposing incidental errors.
- Reject out-of-range and malformed row and column selectors consistently across public methods.
- Validate row- and column-group specifications instead of producing malformed spans or incidental
  indexing failures.
- Reject caption and note styling properties that a selected backend cannot render instead of
  silently ignoring them.
- Forward `color` and `xlim` to plot callbacks independently and identify the resolved cell when a
  callback returns an unsupported object.
- Apply `.fmt(digits=...)` to integer values as well as floating-point values.

### Documentation

- Add troubleshooting and backend styling-support references.
- Reorganize the PDF guide into a sequential tutorial, independent advanced recipes, and a
  task-oriented reference, with deeper navigation and a complete Typst inclusion example.

## [1.2.0] - 2026-07-17

### Features

- Accept strictly validated Python boolean lists and tuples as data-row masks for `i` selectors.

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

[Unreleased]: https://github.com/EinMaulwurf/tytable/compare/v3.0.1...HEAD
[3.0.1]: https://github.com/EinMaulwurf/tytable/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/EinMaulwurf/tytable/compare/v2.2.0...v3.0.0
[2.2.0]: https://github.com/EinMaulwurf/tytable/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/EinMaulwurf/tytable/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/EinMaulwurf/tytable/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/EinMaulwurf/tytable/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/EinMaulwurf/tytable/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/EinMaulwurf/tytable/compare/v1.1.0...v1.2.0
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
