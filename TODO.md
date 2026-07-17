# TODO: Code and documentation audit

Work through these in order where practical: settle and test the implementation
contract first, then update the public documentation to describe the resulting
behaviour. Changes marked for 2.0 may alter valid existing output and must not be
released in a 1.x minor or patch release.

## Bugs and implementation contracts

- [ ] **Validate media input cardinality.** For `.images(paths=...)` and
  `.plot(data=...)`, define one consistent rule for mapping values to the
  resolved row-major cell selection (prefer exactly one item per selected cell,
  unless deliberate broadcasting is added). Reject too few or too many items
  with a clear `ValueError`; do not silently leave image cells unchanged or
  expose an incidental `IndexError`. Add tests for multiple rows and columns,
  empty selections, short inputs, and extra inputs.

- [ ] **Validate formatting options.** Reject unknown `num_fmt` values instead
  of silently falling back to decimal. Validate that `digits` is a non-negative
  integer (and not `bool`), and validate that `fn` is callable and returns an
  appropriate sequence before consuming its result. Add call-time or
  render-time errors consistently and document where they occur.

- [ ] **Validate selectors consistently.** Reject out-of-range integer row and
  column positions, boolean `pl.Series` selectors whose length differs from the
  source DataFrame, and invalid elements in mixed selector lists. Ensure all
  public methods use the same rules and error messages. Decide whether the
  implemented but undocumented `i="~groupi"` selector is supported public API;
  document it if so, otherwise remove or keep it strictly internal.

- [ ] **Validate grouping specifications.** Require run-length `i` lists to
  match the number of data rows, validate dictionary row positions, and define
  behaviour for empty inputs and `None` labels. Validate column positions,
  overlapping groups, duplicate columns, and noncontiguous group spans rather
  than allowing malformed output or incidental indexing failures.

- [ ] **Make caption and note styling honest.** Audit every property accepted
  for `i="caption"` and `i="notes"` across Typst and HTML. Implement properties
  that should be supported, and reject unsupported properties with a targeted
  error instead of accepting and silently ignoring them. Add a backend support
  matrix to tests.

- [ ] **Forward plot callback keywords independently.** Inspect support for
  `color` and `xlim` separately. A callable that accepts `color` but not `xlim`
  must not receive `xlim`; preserve support for `**kwargs`, Matplotlib figures,
  and plotnine objects. Report an invalid callback return type with the selected
  cell or directive context.

- [ ] **Make rendering failures explicit.** Give unsupported output formats a
  deliberate public exception contract. Add context to plot dependency,
  callback, and asset-write failures, and ensure static `.images()` directives
  never require plotting dependencies. Review the `render()` and `save()`
  exception contracts after implementing this.

- [ ] **Normalize backend-specific colors where possible.** Avoid passing a
  valid Typst-only color constructor directly into CSS. Prefer a
  backend-neutral normalized color representation; otherwise reject or clearly
  scope backend-specific expressions through `output=`. Test all accepted
  color forms in Typst and HTML.

### Compatibility-sensitive changes for 2.0

- [ ] **Decide whether `digits` formats integers.** The intuitive behaviour is
  for `.fmt(digits=2)` to render `10` as `10.00`, but 1.x tests currently codify
  that fixed/significant formatting leaves integers unchanged. Preserve and
  document the 1.x behaviour unless an opt-in compatible mode is introduced;
  record any default change under `Breaking` for 2.0.

- [ ] **Resolve duplicate display-name selection.** `set_name()` deliberately
  permits duplicate names, while later name selectors currently match only the
  first occurrence. For 1.x, document the ambiguity and consider a warning. In
  2.0, either select every matching duplicate or reject ambiguous name-based
  selectors consistently.

- [ ] **Redesign generated assets for `.render()`.** Rendering a string can
  currently create `tytable_assets/` in the working directory and retain asset
  state that affects later renders. Consider an explicit asset destination,
  portable embedding by default, or a render artifact containing text and
  assets. Preserve existing 1.x behaviour while documenting its side effects.

- [ ] **Decide whether `.save(..., assets=...)` copies static images.** Static
  `.images()` paths are currently emitted verbatim, whereas `assets=` manages
  only generated plots. Preserve that 1.x contract; for 2.0 consider an
  explicit copy policy such as `copy_images=True` rather than silently changing
  path semantics.

## Documentation

- [ ] **Correct the image dependency guidance.** State consistently in the
  README, guide, and docstrings that only `.plot()` requires the `images`
  extra; `.images()` embeds references to existing files without optional
  Python dependencies.

- [ ] **Correct and expand asset-path documentation.** Explain that `assets=`
  controls generated plot files only, while `.images()` paths are neither
  copied nor checked and are emitted as supplied. Document how paths resolve
  from saved Typst/HTML files and within the Typst project root.

- [ ] **Document rendering side effects.** Explain where `.plot()` writes files
  during direct `.render()` calls, how `.save()` chooses its default and custom
  asset directories, and how retained asset state can affect subsequent renders
  of the same table. Keep this synchronized with any future asset redesign.

- [ ] **Document the final media contract.** After cardinality validation is
  implemented, describe row-major assignment, required `paths`/`data` lengths,
  path existence policy, supported callback signatures, forwarded keywords,
  accepted plot return types, and when media is materialized.

- [ ] **Correct public exception documentation.** In particular, say that only
  plot directives can raise the optional-dependency `ImportError`; document
  unsupported output errors, selector/group validation failures, formatter
  failures, plot callback errors, and asset I/O errors for `render()` and
  `save()`.

- [ ] **Document numeric formatting precisely.** Describe the allowed
  `num_fmt` values and `digits` range, when validation occurs, the transform
  order, and the 1.x integer behaviour. Avoid describing `digits` as universal
  “numeric precision” while integers are intentionally unchanged.

- [ ] **Create one authoritative selector reference.** Include every supported
  row and column selector, method-specific defaults (`style(i=None)` means all
  rows while formatting/media default to body rows), range rules, mask-length
  requirements, regex behaviour and length limit, renamed/duplicate column
  semantics, row-group coordinates, and the difference between original and
  final visible rows.

- [ ] **Document grouping boundaries and examples.** Cover exact run-length
  list size, valid row insertion positions, delimiter requirements, overlapping
  and noncontiguous column groups, empty inputs, `None` labels, and the order of
  stacked column-group rows.

- [ ] **Document supported color forms and backend scope.** List bundled names,
  hex variants, and allowed safe constructors. Explain which forms are
  portable to HTML and when to use `output=("typst",)`.

- [ ] **Document the exported `THEMES` registry.** List its keys and callable
  shapes, explain that theme functions mutate and return the table, and keep the
  typed `.theme_*()` methods as the recommended interface.

- [ ] **Document pipeline data contracts.** Expand the docstrings for
  `BuiltTable`, `_BuildState`, and `TypstRenderOptions` with field-level
  invariants: coordinate systems, inserted row-group rows, trusted versus
  escaped markup, `nhead`, style-grid/line indexing, units, valid option values,
  backend scope, and option precedence.

- [ ] **Remove dangling internal guide references.** Replace references such as
  “guide 06 §1”, “guide 09”, and “guide 15 §2” with self-contained rationale or
  links to real, stable repository documents.

- [ ] **Add only targeted why-comments.** Explain the coordinate transformation
  around inserted row groups, escaping/trusted-markup ownership between the
  formatting and resolve stages, plot asset-directory selection and retained
  state, and why cell-style properties overwrite while line directives append.
  Do not add comments to straightforward helpers merely to increase coverage.

- [ ] **Add a standalone static-image example.** Demonstrate `.images()` without
  importing Matplotlib or installing the optional extra, including a correct
  relative path from the saved fragment.

- [ ] **Add a troubleshooting section.** Cover Typst project roots, missing
  optional dependencies, selector validation errors, escaping versus raw
  markup, generated plot paths, static image paths, and the difference between
  HTML previews and compiled Typst layout.

- [ ] **Document backend styling support.** Provide a compact matrix for cell,
  caption, and note properties across Typst, HTML, and ASCII after unsupported
  meta-style behaviour has been fixed.

- [ ] **Improve the public note type contract.** Consider a public `TypedDict`
  or equivalent for note dictionaries so `text`, `marker`, `i`, and `j` are
  discoverable to type checkers and IDEs; keep the prose schema and examples in
  sync.

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
