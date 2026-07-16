### Documentation delivery and discoverability

- **Deferred:** provide searchable, linkable HTML documentation alongside
  the PDF. Keep `docs/main.typ` and the runnable Python examples as the single
  documentation source; do not introduce a separately maintained MkDocs,
  Sphinx, pdoc, or Markdown manual. Compile the prose, headings, links, code,
  and API reference to semantic HTML using Typst's HTML target. For each
  example result, use a target-aware helper that emits the normal `#include`
  for PDF and wraps the included Typst fragment in `html.frame(...)` for HTML,
  preserving the actual paged Typst rendering as inline SVG. Give the frame an
  explicit width matching the PDF content area so percentage-based tables have
  the same layout context, then scale it responsively with CSS. Initially ship
  one continuous HTML page with heading anchors, a table of contents, and a
  prominent direct PDF link; consider a multi-page Typst bundle only if the
  single page becomes unwieldy. Make page setup, page breaks, title-page layout,
  and other print-only constructs target-aware. Pin the Typst version in CI and
  add HTML smoke tests because HTML and bundle export are still experimental.
  Optionally publish the generated `api.json` and a short `llms.txt` index for
  coding agents rather than duplicating the guide. As a small interim fix, use
  an `<object>` with useful fallback content and a direct PDF link on the
  current Pages site. This was discussed with the user and intentionally
  deferred on 2026-07-16.

---

# TODO: Missing features (from tinytable comparison)

> **Reference:** the R original lives at `/home/debian/git/tinytable/` (source in
> `R/`). When implementing any item below, read the corresponding tinytable file
> for behaviour and edge cases — the goal is feature parity within tytable's
> Typst-first scope, not a 1:1 port. See `tinytable/CLAUDE.md` for the R
> architecture and `tinytables_python_guide/02_scope_and_decisions.md` for what
> is deliberately out of scope (LaTeX/Word/PDF/Markdown/Tabulator/Quarto/ANSI
> are intentionally excluded).

## Medium value

### Feature: column hiding / subset

No way to drop a column at table level without filtering the frame first (which
loses the original index → column mapping used by selectors). Add a `.hide(j=…)`
selector. typ-tables calls this `cols_hide`. See `/home/debian/git/tinytable/R/subset.R`.
Do not add anything to the `tt()` factory.

Implement hiding as a deferred projection near the end of `build()`, after
selectors and other intent have resolved against the original columns. Filtering
`table._data` earlier would make numeric and name-based selectors change meaning.
The projection needs an old-column → new-column map and must update all
column-indexed output: body/header matrices, inferred alignments, per-column
widths, `style_grid`, vertical line coordinates, and column-group rows. It must
also shrink or discard colspans that cross hidden columns and recompute the
full-width colspan used by row-group labels. Footnote and image markers can be
inserted before projection and naturally disappear with a hidden target.

Column groups need explicit care: the group label is stored only in the first
cell of its span, with empty continuation cells after it. If that first column
is hidden while later columns remain, the label must move to the first retained
column rather than disappear. Tests should cover selectors recorded both before
and after `.hide()`, renamed columns, widths, styles and border lines, column and
row groups, spans, notes, images/plots, hiding all columns, repeated `.hide()`
calls, and all three renderers.

## Nice-to-have (deferred in the guide)

### Feature: decimal-point alignment

- **Deferred:** align numeric columns on the decimal separator rather than
  aligning whole cell boxes, including values with different precision and
  scientific notation. Typst does not currently provide native decimal-point
  alignment. The `@preview/zero` package can add it through a scoped table show
  rule and can also align exponent components, but this would introduce a Typst
  package dependency. Typst downloads preview packages on first use, which is
  unsuitable for uncached offline/server builds; supporting those deployments
  would require documenting and maintaining a pre-populated package cache or
  vendoring the package alongside saved output. Revisit if native Typst support
  lands or the dependency and offline-deployment trade-off becomes worthwhile.

### Feature: `set_option()` / config mechanism

The guide parks this ("can come later"). A thin global-defaults mechanism for
`escape` / `digits` / `theme` / `width`. See tinytable's `getOption(
"tinytable_*" )` cascade — `/home/debian/git/tinytable/R/package.R` and the
`get_option` calls throughout `R/tt.R`, `R/format_tt.R`, `R/style_tt.R`.

### Feature: `quarto_compat` flag

Drop the `#figure(...)` wrapper and do `#block` → `block` so the fragment can be
embedded in Quarto-Typst output. Guide §6.9 defers this. See
`/home/debian/git/tinytable/R/typst_finalize.R`.

## Known correctness edge cases (not features)

- `figure=False` + `multipage` emits a possibly-invalid `#set page(breakable:
  …)` (`_render_typst.py:118-120`). No test exercises this combination.
- `fmt(i="header")` is silently dropped — `data_body` contains only body rows,
  so format directives targeting the header never apply. Low priority (format
  column names in polars, or via `colnames_override`).
- HTML column-name double-escaping — column names containing `&`, `<`, or `>`
  are escaped twice in HTML output. `tt(df, colnames_override={"x": "X<Y"})`
  renders as `<th>X&amp;lt;Y</th>` instead of `<th>X&lt;Y</th>`. Reproduces via
  both `colnames_override` and `.set_name()`. Root cause: `escape_html` is
  applied to `colnames_display` in `_resolve.py` (`build`), then the HTML
  renderer escapes the already-escaped string again. The Typst path is
  unaffected (it emits names inside `[...]` content mode, where re-escaping is
  harmless). Fix: either skip the pre-escape for HTML in `build`, or have
  `HtmlRenderer` detect already-escaped names.
