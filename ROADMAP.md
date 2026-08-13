# Roadmap

This is the single backlog for unresolved bugs, improvements, and ideas. Completed work belongs in `CHANGELOG.md`, not here.

## Bugs

- [ ] Emit HTML `<caption>` before `<colgroup>`.
- [ ] Render a sensible ASCII representation for zero-column tables.

## Small improvements

- [ ] Add HTML table semantics: scoped column and row headers, accessible column groups, and caption/note relationships.
- [ ] Normalize or reject blank and whitespace-only group labels.
- [ ] Remove duplicate semicolons from generated inline CSS.
- [ ] Use an absolute README image URL so the image renders on PyPI.
- [ ] Run lint, type checking, and tests in the tag-triggered release workflow before publishing.
- [ ] Add dependency and security scanning.

## Possible features

These are plausible additions within the package's current scope, not commitments; any or none of them may be implemented.

- [ ] Add `.hide(j=...)` as a deferred column projection so all selectors continue to resolve against source columns; projection must update widths, styles, borders, groups, spans, notes, and media across every renderer.
- [ ] Add `.validate()` and `.explain()` for resolved selections, overridden intent, backend limitations, media cardinality, asset policy, and estimated output size; later add `.lint()` for suspicious but valid tables.
- [ ] Add CSS classes and custom properties for site integration, responsive layouts, and dark mode.
- [ ] Add native Typst vector sparklines and data bars without requiring Matplotlib.
- [ ] Add duration and unit formatters, including SI prefixes and accessible accounting conventions.
- [ ] Accept the DataFrame interchange protocol through `pl.from_dataframe()` while keeping Polars as the internal representation and selector language.
- [ ] Add semantic row and column roles such as `total`, `measure`, `unit`, and `key`, with matching Typst emphasis and HTML semantics.
- [ ] Add accessible conditional visual encodings such as scales, thresholds, symbols, and data bars with deliberate fallbacks for each backend.
- [ ] Add an explicitly lossy Markdown renderer with documented behavior for groups, spans, notes, images, multiline content, and raw markup.
- [ ] Improve ASCII rendering for column groups, spans, and multiline cells where practical.
- [ ] Publish searchable HTML documentation from the existing Typst sources without maintaining a second manual.

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
- [ ] Revisit decimal-point alignment if Typst gains native support or offline package deployment becomes practical.
- [ ] Reassess GPL-3.0-only licensing if broader corporate adoption becomes a project goal and copyright ownership permits a change.
