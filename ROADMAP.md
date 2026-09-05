# Roadmap

This is the single backlog for unresolved bugs, improvements, and ideas. Completed work belongs in `CHANGELOG.md`, not here.

## Audit follow-up: correctness in 3.x

Work through these independently, starting with escaping. Preserve the documented 3.x API; future removals do not replace fixes for currently supported behavior.

- [ ] Fix the chained-formatting escaping bypass: invalidate prior escaped/trusted status as soon as a transform replaces content, before line-break generation or explicit escaping. Add regressions for `.fmt(linebreak="|").fmt(fn=lambda values: values, linebreak="|")` with HTML/Typst metacharacters in source values and for repeated explicit escaping with table-wide escaping disabled.
- [ ] Preserve Decimal precision throughout semantic formatting, including scaling and magnitude calculations before final rounding. Cover `Decimal("12345678901234567890123456789.12")` and a reduced ambient Decimal context; verify the shared numeric formatter consumers.
- [ ] Preserve large integers in the supported `.fmt(digits=..., num_fmt=...)` implementation instead of converting through float. Cover `9007199254740993` with zero decimal places and precision-sensitive significant/scientific output.
- [ ] Correct Typst column-name header span rendering: emit the accepted span and omit covered cells consistently, rather than ignoring header spans while suppressing covered body data. Cover header colspans and define valid header-rowspan boundaries consistently with the documented 3.x contract.
- [ ] Preserve HTML body rows fully covered by rowspans. A one-column table containing `A, B, C` with `rowspan=2` on `A` must retain the empty second `<tr>` so the span does not extend into C's row.

## Audit follow-up: concise v4 API

Prioritize these over adding convenience APIs. Each checkbox is a separate work item. Breaking changes belong in v4, with migration guidance and a `Breaking` changelog entry; retain compatibility in 3.x. Check both the manual included by `docs/main.typ` and `docs/agent-guide.md` for each public change.

- [ ] Remove public `colspan` and `rowspan` from `.style()`. Keep spans internal to `.group(j=...)` column headings and `.group(i=...)` row sections; deliberately stop supporting arbitrary spreadsheet-style cell merging. Document the migration and remove obsolete public-span tests without losing internal group-span coverage.
- [ ] Complete the already announced removal of `.fmt(digits=..., num_fmt=...)`, leaving semantic formatters passed through `fn` as the numeric-formatting API. Migrate introductory examples to `number()`, `currency()`, and related factories, and remove the duplicate numeric implementation after preserving its 3.x behavior.
- [ ] Separate whole-table `width` from per-column widths and replace sum-dependent numeric normalization with explicit width/weight semantics. First resolve the current backend discrepancy: `width="3cm"` means each column in Typst but the whole table in HTML. Specify migration behavior for scalar fractions, lengths, mixed lists, and `[1, 1]` versus `[0.4, 0.4]`; assess any compatible 3.x correction separately.
- [ ] Remove legacy `gutter`, retaining explicit `column_gutter` and `row_gutter`. Column spacing must not disappear merely because a grouped table gains a cell background. Keep cell padding as a distinct inside-cell spacing control.
- [ ] Remove `.plot(color=..., xlim=...)` callback-argument forwarding and signature inspection; let callers configure plots in their callback or with `functools.partial`. Retain embedding, selection, and image dimensions, and complete the already announced `fun` to `fn` rename with migration examples.
- [ ] Remove redundant `compact=True` formatter options in favor of `notation="compact"`, including forwarding options on currency and unit formatters. Preserve compact formatting capabilities while eliminating conflicting ways to select the same notation.
- [ ] Replace mutually exclusive `si_prefix` and `iec_prefix` booleans with one unit-prefix choice, provisionally `prefix_system=None | "si" | "iec"`. Define its interaction with notation and cover existing SI/IEC output and rounding-boundary behavior.
- [ ] Evaluate removing `.group(delimiter=...)` in favor of explicit `.group(j=...)` plus display labels, moving name parsing into a recipe. This is a lower-priority candidate, not a settled removal: evaluate migration for nested headers, empty parts, and repeated child labels across different parents before deciding.

Retain stable source selectors, display-only `.show_columns()` and naming, cell-wise `where`, themes, and the separate render/save/compile operations: these serve distinct purposes. New convenience proposals below should justify their API and maintenance cost against this scope before implementation.

## Small improvements

- [ ] Add HTML table semantics: scoped column and row headers, accessible column groups, and caption/note relationships.
- [ ] Normalize or reject blank and whitespace-only group labels.
- [ ] Remove duplicate semicolons from generated inline CSS.
- [ ] Use an absolute README image URL so the image renders on PyPI.
- [ ] Run lint, type checking, and tests in the tag-triggered release workflow before publishing.
- [ ] Add dependency and security scanning.

## Possible features

These are plausible additions within the package's current scope, not commitments; any or none of them may be implemented.

- [x] Add `.show_columns(j, invert=False)` as a display-only column projection so all selectors continue to resolve against source columns; preserve source order and update widths, styles, borders, groups, spans, notes, and media across every renderer.
- [ ] Add `.validate()` and `.explain()` for resolved selections, overridden intent, backend limitations, media cardinality, asset policy, and estimated output size; later add `.lint()` for suspicious but valid tables.
- [ ] Add CSS classes and custom properties for site integration, responsive layouts, and dark mode.
- [ ] Add native Typst vector sparklines and data bars without requiring Matplotlib.
- [x] Add duration and unit formatters, including SI prefixes and accessible accounting conventions.
- [ ] Accept the DataFrame interchange protocol through `pl.from_dataframe()` while keeping Polars as the internal representation and selector language.
- [ ] Add semantic row and column roles such as `total`, `measure`, `unit`, and `key`, with matching Typst emphasis and HTML semantics.
- [ ] Add accessible conditional visual encodings such as scales, thresholds, symbols, and data bars with deliberate fallbacks for each backend.
- [ ] Add an explicitly lossy Markdown renderer with documented behavior for groups, spans, notes, images, multiline content, and raw markup.
- [ ] Improve ASCII rendering for column groups, spans, and multiline cells where practical.
- [ ] Publish searchable HTML documentation from the existing Typst sources without maintaining a second manual.
- [ ] Add backend-translated mini-markup in cells (bold, code, links) so default escaping can stay on while authors emphasize parts of a value.
- [ ] Add `formatters.link()` to render URL columns as native links, and a list formatter that renders sequence cell values as bulleted multi-line cells.
- [ ] Add trailing-zero trimming and value-inferred digit defaults to numeric formatting.
- [ ] Add group-aware zebra striping that alternates the background per row group instead of per source row, designed as theme data rather than a callback registry.
- [ ] Add table-level font family and font size controls to complement per-cell `fontsize`.
- [ ] Add presentation-only collapsing of consecutive duplicate values in key columns while source-row selectors stay stable.
- [ ] Add custom Typst figure kinds so separate table series can number as Table A1, B1, and so on.
- [ ] Export the internal snapshot helpers as a public `tytable.testing` module so users can test their generated tables the same way this package tests its own.
- [ ] Add `tt.stack()` to compose multiple tables into one figure vertically or horizontally with shared assets and a single caption.
- [ ] Add render-time display ordering as intent (`.order_by(j=...)` or an explicit order list) so stable source-row selectors remain valid, unlike sorting the DataFrame before construction.
- [ ] Add a `tt.crosstab()` factory for contingency tables with optional row and column totals.
- [ ] Add first-class sequential and diverging background color scales with colorblind-safe palettes, specified as data rather than callbacks.
- [ ] Add wide-table autopilot that estimates rendered width and then resizes, rotates, or warns, as a companion to `.validate()` / `.explain()`.
- [ ] Add convenience highlight methods (`.highlight_max()`, `.highlight_min()`, `.highlight_top(n)`) and named `.heatmap()` / `.color_scale()` / `.data_bars()` methods over the planned scale and data-bar data.
- [ ] Add `formatters.bool()` (✓/✗, ●/○, yes/no with per-value color), `formatters.ordinal()`, `formatters.rating()`, `formatters.relative_time()`, and `code()`/`email()` wrappers alongside the planned `link()` formatter.
- [ ] Add row-wise formatter contexts (`pct_change()`, `cumsum()`, `share_of_total()`, `share_of_row()`) that read neighboring or whole-column values, extending the column-wise `fn` model.
- [ ] Add `.head(n)`, `.tail(n)`, and `.slice(start, end)` preview truncation with a visible ellipsis row.
- [ ] Add `.transpose()` to swap rows and columns (distinct from the page-level `.rotate()`).
- [ ] Add `.add_index()` / `.add_row_numbers()` for a leading row-number column.
- [ ] Add `.move(j=...)` / `.order_cols()` to reorder display columns while keeping source-name selectors valid.
- [ ] Add `.freeze()` for sticky headers (and optional first column) in HTML, mapping to repeated table headers in Typst.
- [ ] Add `.add_total()`, `.add_subtotal()`, and `.add_stats()` summary rows over numeric columns, aligned with row-group separators.
- [ ] Add `.to_dataframe()` returning the resolved, formatted display grid as a Polars frame.
- [ ] Add `.to_clipboard()` (TSV) and `.to_csv()` (raw data export).
- [ ] Add standalone full-HTML document rendering so saved previews are shareable files rather than `<table>` fragments.
- [x] Accept Polars selectors in `j` (e.g. `j=cs.numeric()`, `j=pl.selectors.by_dtype(...)`), unifying the column-selector vocabulary with `where`; retain Boolean Polars expressions as the data-driven selector vocabulary for `i`.
- [ ] Add `.register_theme(name, fn)` so users can define base appearances beyond the four built-ins.
- [ ] Add dark variants of the built-in themes (Typst-side, complementing the planned HTML dark mode).
- [ ] Add `.summary()` as a lighter diagnostic sibling to `.explain()` describing the resolved grid, dtypes, null counts, and overrides.
- [ ] Add `.preview()` returning rendered source plus an estimated width for the wide-table autopilot.
- [ ] Add `.facet(by=...)` / `tt.panel(...)` to render several tables stacked with a shared caption and per-panel headings.
- [ ] Add `.add_source(...)` and `.add_n()` provenance footers, plus `.note_where(...)` sugar over targeted notes.

## Design ideas

These are broader or less-settled directions that would require more evidence and design work, not planned features.

- [ ] Evaluate reusable `ColumnSpec` and `TableSpec` objects for definitions shared across multiple tables while keeping method chains first-class.
- [ ] Define whether emitted Typst markup has a compatibility contract and introduce a format version only if users need stable long-lived includes.
- [ ] Replace `escaped_cells` and `image_cells` with a small internal tagged-string representation if it measurably simplifies the pipeline; do not introduce a public cell-content hierarchy without demonstrated demand.
- [ ] Consider a stable renderer extension contract only after resolved cell content is backend-neutral.
- [ ] Explore semantic summary rows before adding aggregation conveniences such as `.total_row()`.
- [ ] Explore `tt.diff(before, after, keys=...)` with explicit contracts for duplicate keys, tolerances, missing values, and schema changes.
- [ ] Consider serializable table specifications only for a versioned declarative subset that excludes arbitrary callbacks, expressions, plots, and finalizers.
- [ ] Consider a small CSV/JSON/Parquet-to-Typst CLI and Quarto integration without duplicating the Python API as flags.
- [ ] Wait for native Typst support before adding decimal-point alignment; track [typst/typst#170](https://github.com/typst/typst/issues/170) for column alignment, [typst/typst#3269](https://github.com/typst/typst/issues/3269) for number formatting, and [typst/typst#1093](https://github.com/typst/typst/issues/1093) for locale-aware number formatting. The [Zero package](https://typst.app/universe/package/zero/) demonstrates a package-level solution, but tytable should avoid a Typst Universe runtime dependency so generated output remains suitable for airgapped environments; revisit once the required upstream APIs are stable.
- [ ] Reassess GPL-3.0-only licensing if broader corporate adoption becomes a project goal and copyright ownership permits a change.
- [ ] Evaluate statistical model-summary tables (coefficients, standard errors or confidence intervals, significance stars, goodness-of-fit footer) for statsmodels-style outputs as the publication-ready niche Typst currently lacks.
- [ ] Evaluate an exploratory HTML mode with a tiny dependency-free sortable and filterable preview while keeping static output unchanged.
- [ ] Evaluate emitting the table's style tokens as Typst `#let` variables so the including document can re-theme a generated fragment without regenerating it.
- [ ] Evaluate a LaTeX renderer deliberately rather than by accretion; it would dilute the Typst identity and double maintenance for math, spans, and borders.
- [ ] Decide whether row-wise formatter contexts belong in `fn` or a distinct formatter contract.
- [ ] Extend the planned `tytable.testing` to export resolved `BuiltTable` snapshots (JSON golden files), not just rendered strings.
