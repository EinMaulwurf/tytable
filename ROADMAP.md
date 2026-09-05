# Roadmap

This is the single backlog for unresolved bugs, improvements, and ideas. Completed work belongs in `CHANGELOG.md`, not here.

## Audit follow-up: correctness in 3.x

Work through these independently, starting with escaping. Preserve the documented 3.x API; future removals do not replace fixes for currently supported behavior.

- [x] Fix the chained-formatting escaping bypass: invalidate prior escaped/trusted status as soon as a transform replaces content, before line-break generation or explicit escaping. Add regressions for `.fmt(linebreak="|").fmt(fn=lambda values: values, linebreak="|")` with HTML/Typst metacharacters in source values and for repeated explicit escaping with table-wide escaping disabled.
- [x] Preserve Decimal precision throughout semantic formatting, including scaling and magnitude calculations before final rounding. Cover `Decimal("12345678901234567890123456789.12")` and a reduced ambient Decimal context; verify the shared numeric formatter consumers.
- [x] Preserve large integers in the supported `.fmt(digits=..., num_fmt=...)` implementation instead of converting through float. Cover `9007199254740993` with zero decimal places and precision-sensitive significant/scientific output.
- [x] Correct Typst column-name header span rendering: emit the accepted span and omit covered cells consistently, rather than ignoring header spans while suppressing covered body data. Cover header colspans and define valid header-rowspan boundaries consistently with the documented 3.x contract.
- [x] Preserve HTML body rows fully covered by rowspans. A one-column table containing `A, B, C` with `rowspan=2` on `A` must retain the empty second `<tr>` so the span does not extend into C's row.

## Audit follow-up: concise v4 API

Prioritize these over adding convenience APIs. Each numbered subsection is an independently implementable work item; the two formatter-option changes may follow one another. Breaking changes belong in v4, with migration guidance and a `Breaking` changelog entry; retain compatibility in 3.x. The completed correctness fixes above must remain covered by regression tests wherever their behavior survives the cleanup.

For every item, update public signatures, docstrings, typing examples in `tests/typecheck/public_api.py`, affected examples and snapshots, the manual included by `docs/main.typ` (`docs/reference.typ`, `docs/tutorial.typ`, and `docs/guides.typ`), and `docs/agent-guide.md`. Generated API signatures come from `docs/build_examples.py`; do not hand-edit generated documentation. Run lint, type checking, and the non-image suite in that order; also run image tests for plotting changes and available Typst compilation tests for layout changes. Record completed work in the changelog.

### V4-1: remove public cell spans

- [x] Remove `colspan` and `rowspan` from `.style()` and `StyleDirective`; passing these removed keywords should fail at the public call boundary. Do not introduce a replacement manual-merge API.
- Implementation: update `_tytable.py`, `_directives.py`, and `_styling.py` validation/property collection. Simplify user-span projection and validation in `_resolve.py` only where no longer needed. Preserve internal group colspan generation, covered-cell handling, and border resolution in both renderers; do not delete all span machinery merely because its public controls disappear.
- Acceptance: nested `.group(j=...)`, delimiter-created groups, `.group(i=...)`, group styling, and group borders still render correctly. Cover `.show_columns()` hiding the original first member of a column group or the first source column of a row group. No ordinary data values should disappear through user-configured spans in v4. Replace obsolete public-span tests with internal group coverage where appropriate.
- Migration: shared headings use `.group(j={label: columns})`; labeled row sections use `.group(i=...)`. Explain that these are semantic alternatives, not exact replacements for every spreadsheet-style merged layout.

### V4-2: one numeric-formatting API

- [x] Remove `digits` and `num_fmt` from `.fmt()` and `FormatDirective`, and remove the legacy numeric stage and its exclusive helpers from `_format.py`. Keep semantic formatter factories in `_formatters.py`, exported through `tytable.formatters` and applied via `.fmt(fn=...)`.
- Preserve `i`, `j`, `where`, `output`, `fn_values`, `replace`, `linebreak`, `math`, and escaping. The remaining per-directive order is callback, replacement, line breaks, math, escaping. Remove validation specific to combining legacy `digits` with typed callbacks; retain callback type/cardinality validation and original typed input by default. Do not expand this task into a redesign of callbacks or markup.
- Migration: `.fmt(digits=n)` becomes `.fmt(fn=number(digits=n, grouping=False))`; significant formatting uses `notation="significant"`. Explicitly document differences: semantic formatters have different missing-value/type policies, significant notation requires positive digits, and semantic scientific output is textual `e` notation rather than the legacy backend-native multiplication/superscript markup. Do not silently bless changed snapshots as equivalent output; provide a callback recipe where preserving the old presentation matters.
- Acceptance: cover `number`, `currency`, `percent`, `date`, `duration`, and `unit` with supported typed columns, conditional selections, grouped rows, output filters, and chained display callbacks. Retain precision and escaping regressions. Retire legacy-only tests and update the guide's introductory examples so the removed API is no longer taught.

### V4-3: clarify width semantics while retaining proportions

- [x] Separate whole-table `width` from per-column sizing, using `column_widths` as the proposed new parameter. Preserve convenient numeric proportions and the existing normalization of all-numeric lists whose sum exceeds 1; removing that behavior is no longer part of this task.
- Proposed contract: `width` is `None`, a finite non-negative fraction of the available line width, or a length string describing the whole table. `column_widths` is `None` or a sequence with one entry per source column. Preserve sequence validation and normalization: `[2, 1]` becomes approximately `[2/3, 1/3]`, `[1, 1]` becomes `[0.5, 0.5]`, and `[0.2, 0.1]` stays unchanged. Mixed lengths/fractions/`None` remain unnormalized. Document the threshold explicitly; do not add a mandatory weights wrapper or require users to calculate percentages.
- Before changing rendering, specify how fractional column widths relate to the table's available layout width when both parameters are present, including auto-sized tables. Use the same interpretation in Typst and HTML. Preserve normalization-before-projection for `.show_columns()` unless a separately documented design change is justified; hiding a column must not silently renormalize the surviving fractions. Define empty/all-zero sequences without division by zero.
- Implementation: split storage in `TyTable` and `BuiltTable`, update cloning and `_project_width` in `_resolve.py`, and separate Typst table-container sizing from `_columns_spec`. Update HTML `_table_open` and `_emit_colgroup` accordingly. Keep `.resize()` as uniform scaling of the rendered table/text, distinct from column layout. Do not simply reuse its scaling wrapper to implement table width.
- Acceptance: `width="3cm"` means the whole table in both backends; explicit `column_widths=["3cm", "3cm"]` means two 3 cm columns. Cover scalar fractions, normalized numeric sequences, partial fractions, mixed entries, explicit table width plus columns, hidden columns, and clone independence. Verify compiled Typst layout as well as emitted source and HTML. State any backend limitations for length units rather than pretending Typst `fr` is valid CSS.
- Migration: move legacy `width=[...]` to `column_widths=[...]`. A legacy Typst scalar length applied to every column needs a repeated per-column length sequence; document the intentional correction to scalar-length semantics. Preserve scalar fractional whole-table sizing and proportional convenience.

### V4-4: remove legacy gutter behavior

- [x] Remove constructor `gutter` from both `tt()` and `TyTable`; retain `column_gutter`, `row_gutter`, and cell `padding`. Keep explicit gutters in points for numeric values and as Typst lengths for strings. Default `None` leaves spacing to the normal renderer defaults; do not preserve an implicit grouped-only 2 pt gutter.
- Implementation: remove `column_gutter_explicit` and the grouped/background-dependent fallback in `TypstRenderOptions` and `_emit_table_options`. Remove `BuiltTable.has_background` only if it has no remaining consumer. Emit explicitly supplied column spacing independently of grouping, themes, and backgrounds; avoid changing HTML spacing semantics as an unrelated addition.
- Acceptance: the same explicit gutter survives toggling backgrounds and switching base themes on grouped and ungrouped tables. Cover zero, `None`, valid length strings, invalid/non-finite numbers, row gutters, and padding. Compile representative grouped tables to catch border/track-spacing interactions.
- Migration: replace `gutter=value` with `column_gutter=value`. Documents that relied on the implicit legacy gap must request `column_gutter=2`; explain that the explicit setting applies consistently rather than conditionally.

### V4-5: simplify plot callback configuration

- [x] Rename `.plot(fun=...)` to `.plot(fn=...)` and remove its public `color` and `xlim` options. Call the callback with exactly one positional cell value or matching `data` entry; do not inspect its signature or inject plot-specific keyword arguments.
- Implementation: update `PlotDirective`, `_tytable.py`, and `_images.py`; remove `_callback_kwargs` and forwarding-only validation/helpers/imports when unused. Validate `fn` is callable when registering the directive. Preserve `data` overrides, selectors, row-major cardinality, height/pixel dimensions, backend filters, supported Matplotlib/plotnine results, contextual errors, and existing asset policies.
- Acceptance: callbacks with their own `color`/`xlim` defaults retain those defaults; `functools.partial` and callable objects work; a callback needing an unbound extra argument gets the usual contextual render error. ASCII still emits placeholders without invoking plotting callbacks or importing optional plotting dependencies. Verify rendering and repeated saves do not acquire persistent media state.
- Migration: `.plot(fun=draw, color="red", xlim=(0, 1), ...)` becomes `.plot(fn=partial(draw, color="red", xlim=(0, 1)), ...)`, or use a wrapper function. The removed keyword names must not remain as undocumented aliases in v4.

### V4-6a: one compact-notation option

- [x] Remove `compact` from the semantic `number`, `currency`, and `unit` factories, leaving `notation="compact"` as the single choice. These are formatter options, not new options on `.fmt()`.
- Implementation: remove boolean validation, alias conversion, and forwarding from `_formatters.py`; preserve `compact_labels`, threshold selection, rounding-boundary promotion, precision, signs, locale separators, and special-value formatting. Keep percent's existing notation forwarding; it does not need a new compact switch.
- Acceptance: migrate representative `compact=True` cases to `notation="compact"` and require identical results, including custom labels and negative rounding boundaries. Removed keywords fail at factory construction; invalid notation still raises the documented validation error.
- Migration: `number(compact=True)` becomes `number(notation="compact")`, with the same change for currency/unit factories. Omit `compact=False`; preserve any independently selected notation.

### V4-6b: one unit-prefix choice

- [x] Replace semantic `unit()` options `si_prefix` and `iec_prefix` with the proposed `prefix_system: Literal["si", "iec"] | None = None`. Keep this configuration on the formatter, not on `.fmt()`; use the same name in signatures, typing examples, and documentation.
- Implementation: select the existing SI or IEC threshold table from this one value in `_formatters.py`. Reject non-string/non-`None` values with `TypeError` and unknown strings with `ValueError` at factory construction. Retain the rejection of combining any prefix system with `notation="compact"`; preserve other currently supported notation combinations.
- Acceptance: preserve scaling-before-prefix-selection, positive/negative values, zero, null/NaN/infinity handling, accounting, spacing, precision, and promotion across rounding boundaries. Existing SI/IEC cases should produce identical output after keyword migration. Both removed boolean keywords must fail rather than remain hidden aliases.
- Migration: `si_prefix=True` becomes `prefix_system="si"`, `iec_prefix=True` becomes `prefix_system="iec"`, and both false becomes the default `None`. Implement after V4-6a or coordinate the compact-notation validation so neither change reintroduces obsolete options.

### Retained scope

Keep `.group(delimiter=...)`; its proposed removal is withdrawn for now. Preserve its documentation, examples, and regression coverage through all other cleanups. Explicit `.group(j=...)` also continues to accept Polars column selectors and `regex()` for contiguous, non-overlapping groups. Row-group creation retains position mappings or one label per source row; adding predicate-based row-group creation is not part of this cleanup.

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
