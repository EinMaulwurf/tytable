#import "_common.typ": api, api_signatures, docs-table

#pagebreak()

= — Reference <api-reference>

Use this part for task-based lookup. It collects the complete selector rules, method signatures, error contracts, and migration notes.

== Task-oriented API reference

Start here when you know the task but not the method. Methods marked *chainable* mutate the `TyTable` and return `self`; output methods are terminal.

#docs-table(
  columns: (1.55fr, 2.35fr, 1.1fr),
  align: (left, left, left),
  table.header(text(weight: "bold")[Task], text(weight: "bold")[Use], text(weight: "bold")[Result]),
  [Create],
  [`tt(...)`],
  [`TyTable`],
  [Style cells],
  [`.style(...)`],
  [chainable],
  [Format values],
  [`.fmt(...)`],
  [chainable],
  [Group rows/columns],
  [`.group(...)`],
  [chainable],
  [Rename headers],
  [`.set_name(...)`],
  [chainable],
  [Choose a base theme],
  [`.theme_striped()` / `.theme_grid()`],
  [chainable],
  [Adjust table layout],
  [`.rotate()` / `.resize()` / `.multipage()`],
  [chainable],
  [Add plots/images],
  [`.plot(...)` / `.images(...)`],
  [chainable],
  [Post-process output],
  [`.finalize(...)`],
  [chainable],
  [Get a string],
  [`.render(...)`],
  [`str` (terminal)],
  [Write a file],
  [`.save(...)`],
  [`None` (terminal)],
)

=== Authoritative selector reference

`.style()`, `.fmt()`, `.plot()`, `.images()`, and targeted `NoteDict` entries share `i` and `j`; `.style()`, `.fmt()`, and targeted notes additionally accept the cell-level `where` selector. `.set_name()` and `.show_columns()` share `j`. Omitting `i` selects every genuine source-data row for method calls; in a note, at least one of `i`, `j`, or `where` makes it targeted, and an omitted axis covers the corresponding data region. With `j=None`, every column is selected (`.plot()` and `.images()` require an explicit `j`; `.set_name()` instead accepts a full-list replacement or a source-to-display mapping).

#docs-table(
  columns: (auto, 1.5fr, 1fr),
  align: (left, left, left),
  table.header(text(weight: "bold")[Selector], text(weight: "bold")[Example], text(weight: "bold")[Meaning]),
  [`i`],
  [`0`, `2`, `[0, 2]`, `range(5)`],
  [0-based source DataFrame row(s)],
  [`i`],
  [`"header"`, `"data"`],
  [column names or genuine source rows],
  [`i`],
  [`"all"`],
  [the complete displayed grid],
  [`i`],
  [`"groupi"`],
  [row-group separator rows],
  [`i`],
  [`groupi(label="A")`],
  [row-group separators with the exact registered label `"A"`],
  [`i`],
  [`rowgroup(label="A")`],
  [source-data rows belonging to row groups labelled `"A"`],
  [`i`],
  [`"groupj"`],
  [all column-group header rows],
  [`i`],
  [`groupj(level=0)`],
  [one nested column-group header level],
  [`i`],
  [`pl.col("Score") > 80`],
  [Polars expression evaluated on source data],
  [`i`],
  [`pl.Series(...)`],
  [boolean mask with one value per source row],
  [`i`],
  [`lambda row: ...`],
  [predicate receiving a row dictionary],
  [`j`],
  [`"Score"`, `0`],
  [column name (preferred) or position],
  [`j`],
  [`["Revenue", "Cost"]`, `range(5)`],
  [several columns in one directive],
  [`j`],
  [`cs.numeric()`, `cs.starts_with("rev")`],
  [columns selected from the original Polars schema],
  [`j`],
  [`regex(r"^Q\d+$")`],
  [columns matched by a fail-loud Python regular expression],
  [`j`],
  [`colgroup(label="Results", level=0)`],
  [source columns belonging to matching registered column groups],
  [`where`],
  [`cs.numeric() > 100`],
  [true body cells in `.style()`, `.fmt()`, or a targeted note],
)

Non-negative integer `i` values range from zero through the source DataFrame height minus one. Row-group separators never change what an integer selects. `"header"` is empty when column names are hidden, and `"groupj"` is empty when no column-group rows exist. Import `groupi`, `rowgroup`, and `groupj` from `tytable.selectors` for typed group selectors. `groupi()` selects every row-group separator, while `groupi(label="A")` selects every separator whose original registered label is exactly `"A"`. `rowgroup(label="A")` selects the source-data rows after each matching separator and before the next separator. Repeated labels all match, later formatting of the displayed label does not affect selection, and a missing label raises `ValueError`; a separator after the final source row has an empty member selection. Use `groupj(level=n)` with `.style()` to select one nested column-group header level. Level 0 is the first-created, innermost level nearest the ordinary column names; every later `.group(j=...)` call creates the next outer level above it. Levels retain these identities when `.show_columns()` removes an empty header level. Lists and tuples may mix typed group selectors with integer and string row selectors. `.style()` also accepts `i="caption"` and `i="notes"`; these non-grid targets allow only their documented text-oriented properties.

Data-driven `i` forms have a different coordinate system: a Polars expression, boolean list/tuple, boolean `pl.Series`, or `callable(row_dict) -> bool` is evaluated against the original DataFrame. Masks must be Boolean and have exactly one entry per source row, callable predicates must return a genuine Boolean for every row, and a boolean mask cannot mix booleans with integer selectors. Matching source rows are mapped around inserted row-group separators. Thus use an integer for a stable source-row position, or a predicate/mask when the target depends on source data values. `where` is also evaluated against the original DataFrame; it must return Boolean columns with original source-column names and the source row count. Its true cells are intersected with `i` and `j`, and it cannot target synthetic headers, group rows, captions, or notes.

Integer `j` values range from zero through the column count minus one. Exact string names are case-sensitive and always refer to original DataFrame column names. Polars selectors such as `cs.numeric()`, `cs.string()`, `cs.starts_with(...)`, and `cs.by_dtype(...)` expand against the original source schema and may appear alone or inside a sequence with names and positions. They work in `.style()`, `.fmt()`, `.plot()`, `.images()`, targeted notes, `.set_name()`, `.show_columns()`, and column-group values; an empty selector is an empty selection, except that a column group must be nonempty and contiguous. Arbitrary Polars expressions are not column selectors. Names assigned by `.set_name()` are display-only and never match a selector unless the same string is independently an original column name. This makes duplicate and empty display labels legal and unambiguous. Directives recorded before and after a rename therefore select the same columns. Sequence selections are deduplicated and resolved into displayed column order, so repeated selectors do not target a cell more than once.

On a column-group header row selected by `"groupj"` or `groupj(level=...)`, `j` selects the spanning header cell covering each chosen visible source column. If several selected columns are covered by the same spanning cell, that cell is targeted only once. Without a level qualifier, a source column selects its covering group cell at every column-group level. Per-column alignment values that assign conflicting alignments to the same spanning cell are rejected. A member hidden by `.show_columns()` does not select a group cell that survives over another visible member.

If friendly names should become the actual selector names, rename the Polars DataFrame before constructing the table. The renamed schema then supplies both the source identities and the initial display labels:

```python
df = df.rename({"annual_revenue_usd": "Revenue"})
table = tt(df).fmt(j="Revenue", digits=0)
```

Import `regex` and `colgroup` from `tytable.selectors`. Use `regex(pattern)` for Python `re.search` matching over original DataFrame column names, not display labels or a full match. Each pattern is limited to 500 characters and must match at least one column; invalid patterns and no-match patterns raise `ValueError`. Use `colgroup(label="Results", level=0)` to select the original source columns belonging to every exactly matching registered group at one stable level. Both arguments are required and the label must be nonempty; repeated labels at that level are combined, while missing labels and levels raise `ValueError`. Column-group selectors continue to resolve against the complete registered grouping after `.show_columns()` and may define a later column-group level. A sequence may freely mix exact names, positions, regex selectors, column-group selectors, and Polars selectors, and its result is de-duplicated into source-column order. Polars also provides `cs.matches(pattern)` using its own regex engine; like other Polars selectors, it produces an empty selection when nothing matches. Regex and column-group selectors apply only to `j`, not `i` or `where`.

=== Creating a table

#api("Create", api_signatures.at("tt"))

`data` is a Polars `DataFrame` and is cloned on construction. The constructor options fall into these groups:

#docs-table(
  columns: (1.05fr, 1.9fr, 2.05fr),
  align: (left, left, left),
  table.header(text(weight: "bold")[Concern], text(weight: "bold")[Options], text(weight: "bold")[Notes]),
  [Figure],
  [`figure`, `caption`, `label`, `notes`],
  [captions and labels require `figure=True`],
  [Layout],
  [`width`, `height`, `gutter`, `column_gutter`, `row_gutter`],
  [`width=1` fills the line; lists set each column],
  [Headers],
  [`colnames`],
  [show or hide display headers],
  [Values],
  [`escape`],
  [global safe-markup policy],
)

`width` accepts a finite, non-negative fraction, a Typst length string, or one entry per column in a list or tuple (fractions, strings such as `"3cm"` / `"1fr"`, and `None` may be mixed). `height` sets a finite, non-negative row height in `em`; it does not scale the table like #link(<resize>)[`.resize()`]. `gutter` retains the legacy grouped-table column spacing. `column_gutter` explicitly overrides it for every table layout, while `row_gutter` independently spaces rows; each accepts points as a number or a Typst length string. Numeric formatting is configured separately with `.fmt()`. A note is a string or a `NoteDict`, exported from `tytable`. Its optional keys are `text` (footer text), `marker` (an explicit string or `None`), `i` (row selector), `j` (column selector), and `where` (cell-level Polars expression):

```python
from tytable import NoteDict, tt

significance: NoteDict = {
    "text": "Statistically significant",
    "marker": "*",
    "i": [0, 2],
    "j": "Estimate",
}
table = tt(df, notes=[significance, "Source: model output"])
```

The annotation is optional: it makes these keys and selector types discoverable to type checkers and IDEs, but an unannotated dictionary behaves identically. When `marker` is absent, a note with `i`, `j`, or `where` is numbered automatically; an untargeted note remains unmarked.

Application code should normally construct with `tt(...)` and use `TyTable` for annotations.

=== Formatting and structure

#api("Style", api_signatures.at("style"))

Combines any properties sharing the same selectors. `where` accepts a Polars expression for cell-level selection. `align` uses `l`/`c`/`r`, `alignv` uses `t`/`m`/`b`, `rotate` is a finite number of degrees, and `line` is any combination of `t`/`b`/`l`/`r`. With several columns, `align="llr"` assigns one alignment per column. `fontsize`, `indent`, `padding`, and `line_width` are finite, non-negative values in `em`; `padding` accepts one, two, or four values. `line_style` accepts `solid`, `dashed`, `dotted`, `dash-dotted`, or `none`, and later directives replace earlier styles on the same physical edge. `output` can restrict a directive to one backend or a sequence, such as `"typst"` or `("typst", "html")`.

#api("Format", api_signatures.at("fmt"))

Transforms values in this order: `digits`, `fn`, `replace`, `linebreak`, `math`, then `escape`. `where` restricts all transforms in the directive to individual true body cells. `digits` is either `None` (no numeric formatting) or a non-negative integer; booleans are rejected even though Python treats them as integers. `num_fmt` is `"decimal"`, `"significant"`, or `"scientific"`. Decimal formatting uses `digits` places after the decimal point, significant formatting uses that many significant figures, and scientific formatting uses that many places after the mantissa's decimal point. Both integer and floating-point values are formatted; booleans, nulls, and non-numeric values are left unchanged. Scientific notation uses target-native Typst/HTML markup and a plain-text form in ASCII.

`digits`, `num_fmt`, `replace`, `fn_values`, and whether `fn` is callable are validated immediately when `.fmt()` is called. Selectors are resolved and `fn` results are validated during rendering. By default, `fn` receives each selected column as original typed Python values; `fn_values="display"` instead passes the current display strings, including the result of earlier formatting. The callback must return a non-string sequence of the same length. `replace` then may blank missing values, supply a replacement string, or map old values to new ones. `linebreak` is a literal marker replaced for Typst and HTML output. `math=True` wraps Typst values in math delimiters without changing HTML or ASCII.

Import semantic formatter factories from `tytable.formatters`, call one with its configuration, and pass the returned formatter to `fn`, as in `.fmt(j="Share", fn=percent(digits=1))`. A custom function that already accepts a sequence of values is passed directly as `fn=my_formatter`; use `fn=my_formatter(...)` only when it too is a factory returning that callable. Formatters consume original typed values and should not be combined with `digits`; use the formatter's own `digits` option instead. Custom callbacks can consume the result of `.fmt(digits=...)` by selecting `fn_values="display"`. The German locale preset `locale="de_DE"` produces values such as `1.023,87 €`, while `locale="en_US"` uses English separators. These presets cover separator and currency-placement conventions rather than the complete CLDR locale database.

#api("Format numbers", api_signatures.at("formatter_number"))

`notation` accepts `"fixed"`, `"significant"`, `"scientific"`, `"engineering"`, or `"compact"`. The legacy `compact=True` option selects compact notation. In fixed, compact, scientific, and engineering notation, `digits` sets the maximum decimal places. `min_digits` sets the minimum and defaults to `digits`. Significant notation uses `digits` significant figures. `grouping` inserts thousands marks. You can override locale defaults with `decimal_mark` and `thousands_mark`.

`scale` multiplies each value before rounding. For example, `number(digits=1, scale=1 / 1e6)` displays `2500000` as `2.5`. `rounding` accepts `"half_even"`, `"half_up"`, `"half_down"`, `"up"`, `"down"`, `"ceiling"`, or `"floor"`. The formatter removes a negative sign when a value rounds to zero. Set `normalize_negative_zero=False` to retain the sign.

`compact_labels` maps positive powers of ten to labels. For example, `{3: " thousand", 6: " million"}` supplies long labels. Compact notation promotes a rounded `1000 thousand` value to `1 million`. `accounting` encloses negatives in parentheses. `prefix` and `suffix` add text around finite values. `null` formats nulls and NaNs by default. Set `nan` to format NaNs separately. The `inf` and `negative_inf` options format infinities.

#api("Format currencies", api_signatures.at("formatter_currency"))

Known `EUR`, `USD`, `GBP`, and `JPY` codes use their symbols. The formatter displays another code literally unless `symbol=` overrides it. `symbol_position` accepts `"auto"`, `"prefix"`, or `"suffix"`. German locales use suffix placement in automatic mode. English and default output use prefix placement.

The formatter accepts the number options for precision, notation, separators, grouping, accounting, compact labels, scaling, rounding, and special values. `digits=2` remains the default. Set `digits=None` to use known currency digits, such as zero digits for JPY and three for KWD.

#api("Format percentages", api_signatures.at("formatter_percent"))

Values are multiplied by `scale=100` by default, so `percent(digits=1)` displays `0.6281` as `62.8%`. Set `scale=1` for values that are already percentages. The formatter accepts the number options for precision, notation, separators, grouping, accounting, rounding, negative zero, and special values. German locales add a non-breaking space before `%`. English and default output do not.

#api("Format dates and times", api_signatures.at("formatter_date"))

The formatter accepts Python date, datetime, or time values and applies the `strftime` pattern. `timezone` accepts an IANA name or a `tzinfo` object. Timezone conversion requires timezone-aware datetime values. Dates do not require conversion. Time-only values cannot use conversion. Nulls use the configured `null` text.

#api("Format durations", api_signatures.at("formatter_duration"))

The formatter accepts numeric values in `input_unit` or Python `timedelta` values. The default `style="clock"` uses `HH:MM:SS`, and hours can exceed 24. `style="human"` uses values such as `1d 3h 30m`. `digits`, `min_digits`, `rounding`, and `normalize_negative_zero` control seconds. The `null`, `nan`, `inf`, and `negative_inf` options control special values.

#api("Format values with units", api_signatures.at("formatter_unit"))

The formatter appends `symbol` after a non-breaking space by default. It accepts the number options for precision, notation, separators, grouping, accounting, scaling, rounding, and special values. `si_prefix=True` selects SI prefixes from yocto (`y`) through yotta (`Y`). `iec_prefix=True` selects binary prefixes from kibi (`Ki`) through yobi (`Yi`). The formatter promotes values when rounding crosses the next prefix boundary. SI, IEC, and compact prefixes cannot be combined. Set `space=""` if the symbol must touch the number.

#api("Group", api_signatures.at("group"))

For row groups, pass `{label: row}` or a list with one group value per data row. For spanning column headers, pass `{label: [columns]}` as `j`, or pass a literal string as `delimiter` to split every column name. `j` and `delimiter` are mutually exclusive.

#api("Rename display headers", api_signatures.at("set_name"))

With `j`, `name` is one display name or a list matching the selected columns. Without `j`, pass either the complete list of display names or a mapping from original DataFrame names to display names. The DataFrame remains unchanged, and all `j` selectors continue to use its original column names.

#api("Choose displayed columns", api_signatures.at("show_columns"))

Applies a display-only projection without modifying the DataFrame. `j` accepts names, integer source positions, regex selectors, column-group selectors, Polars selectors, or a mixed sequence, and the result retains source-column order. Set `invert=True` to omit the selection instead. Hidden columns remain available to selectors and conditional formatting, and a later call replaces the previous projection. Per-column widths, groups, spans, styles, notes, and media are projected with the displayed columns for every renderer.

#api("Use default appearance", api_signatures.at("theme_default"))

#api("Add stripes", api_signatures.at("theme_striped"))

#api("Add a grid", api_signatures.at("theme_grid"))

#api("Use plain appearance", api_signatures.at("theme_plain"))

This changes only the base appearance; all other recorded intent survives.

#api("Clone a configured table", api_signatures.at("clone"))

Returns an independently configurable table with separate intent collections and a distinct, cheap Polars DataFrame clone. Recorded selector objects and callbacks are reused by reference and should be treated as immutable configuration. Use clones to derive web, print, or alternative-theme variants from one common base.

#api("Rotate", api_signatures.at("rotate"))

Rotates the whole table by a finite angle. Rotate selected cell content with `.style(rotate=...)`.

#api("Resize", api_signatures.at("resize"))

Scales Typst output by a positive width or height. `direction` is `"down"`, `"up"`, or `"both"`. The method validates these options when called.

#api("Span pages", api_signatures.at("multipage"))

Makes the Typst figure breakable. Header and column-group rows repeat on each page unless `repeat_headers=False`. The `repeat_headers` option must be a Boolean.

=== Plots and images

Only generated plots require the optional `images` extra. `.images()` handles existing files using only the Python standard library. Media is materialized when the table renders or saves, not when the directive is recorded. Media height must be a positive, finite number or an `em` string.

For both methods, tytable resolves `i` and `j` at render time and walks the selection row-major: each resolved row in order, then each resolved column in order. `.images(paths=...)` always requires exactly one path per selected cell. When `.plot(data=...)` is supplied, it likewise requires exactly one item per selected cell; without `data`, the callback receives each selected cell's typed DataFrame value. Empty selections therefore require an empty supplied list. Too few or too many items raise `ValueError` before plotting dependencies are loaded or callbacks run.

#api("Generate plots", api_signatures.at("plot"))

`j` and `fun` are required. The callable receives the typed cell value (or the matching `data` entry) and returns a Matplotlib `Figure` or `plotnine` plot. Pixel dimensions control PNG generation for both backends and override a returned Matplotlib figure's canvas size; `height` independently controls the displayed cell size. `color` and `xlim` are inspected independently: each keyword is forwarded only if the callback declares it or accepts `**kwargs`. Plot callbacks and PNG generation run during `.render()` / `.save()`. Direct Typst and HTML renders embed the generated image bytes in the returned fragment; ASCII uses a text placeholder. `.save()` instead writes external PNG assets.

#api("Embed files", api_signatures.at("images"))

`j` and `paths` are required. Paths are assigned row-major across selected cells. The terminal operation's `static_images` policy determines what happens to them:

- `"copy"` reads local files relative to the Python process's current working directory, gives each unique file a content-hashed name, and copies it under `assets`. This is the `.save()` default.
- `"reference"` emits each path or URL as authored, apart from markup escaping, without checking it. This is the `.render()` default and suits externally managed report assets and remote HTML images.
- `"embed"` reads local PNG, JPEG, GIF, or SVG files and includes their bytes in the Typst or HTML fragment. It creates no static-image asset, but can make the fragment substantially larger.

Copy and embed reject URLs, missing files, and unreadable inputs with the directive, selected cell, and path in the error. Neither mode needs Matplotlib or the optional `images` extra. ASCII output uses a text placeholder without reading the input.

=== Rendering and output

#api("Post-process", api_signatures.at("finalize"))

Registers `fn(rendered: str, output: str) -> str`. Callbacks run in registration order after any renderer and are useful for narrowly scoped integration markup.

#api("Render string", api_signatures.at("render"))

`output` is `"typst"`, `"html"`, or `"ascii"`. Rendering resolves all recorded intent and runs finalizers. The same table can be rendered more than once. See #link(<alternative-backends>)[Alternative backends] for HTML and ASCII usage, including terminal previews with `print(table)`. A direct render of a table with `.plot()` is self-contained: Typst embeds image bytes and HTML uses data URIs. Rendering leaves no persistent files or directories, and repeated calls do not retain a destination from an earlier `.save()`. Embedded plots can make these strings large; use `.save()` when external plot files are preferable. Rendering uses `static_images="reference"` by default. Pass `"embed"` for a self-contained Typst or HTML string. `"copy"` raises `ValueError` because rendering has no output location into which files could be copied.

An unsupported `output` raises `NotImplementedError`. Most selectors are recorded first, so invalid selector types, positions, mask lengths, regexes, and missing columns raise `TypeError` or `ValueError` during `.render()`; grouping specifications and selectors passed to `.set_name()` or `.show_columns()` are validated when those methods are called. Register a column group before using `colgroup(...)` with one of these immediate operations. Formatter option errors are raised by `.fmt()`, while an invalid formatter result raises `TypeError` or `ValueError` during rendering. Only a `.plot()` directive can raise the optional-dependency `ImportError`. A plot callback exception is wrapped in `RuntimeError` with directive and cell context; an unsupported callback return is `TypeError`; and failures to create or write generated assets raise `OSError` with their destination. Exceptions from finalizer callbacks propagate unchanged.

#api("Save file", api_signatures.at("save"))

Creates parent directories and infers the format from `.typ`, `.html`, `.htm`, or `.txt`. The `.txt` suffix selects ASCII. Other suffixes raise `ValueError`; use `.compile()` for PDF, PNG, or SVG output. `assets` controls all externalized media: generated `.plot()` PNGs and `.images()` inputs copied by the default `static_images="copy"` policy. A relative value is resolved from the output file's directory and is also emitted in the fragment; the default is a table-specific sibling `<path.stem>_assets/` directory. Use `static_images="reference"` to retain authored paths without checks, or `"embed"` to include supported static files in the fragment while generated plots remain external. Each save has an independent destination and does not mutate the table or affect a later `.render()` or `.save()` call. Generated plot names and copied static names contain content hashes to avoid collisions; repeated static content is copied once per save. `save()` can additionally raise `OSError` while creating the destination directory or writing the table or an asset. Static copy/embed can raise contextual `OSError` for unreadable files and `ValueError` for URLs or unsupported embedded formats. Other render-time contracts are the same as for `.render()` above.

#api("Compile artifact", api_signatures.at("compile"))

Uses an installed Typst CLI to write PDF, PNG, or SVG and returns `None`, preserving the text-only `render() -> str` contract. Typst source is sent through standard input, generated plots and static images are embedded by default, and no intermediate source or asset directory remains. `root` defaults to the Python working directory and controls authored references and raw Typst content; `font_paths` adds font directories, `pages` selects output pages, and `ppi` controls PNG resolution. Multi-page PNG/SVG output requires `{p}` in the output filename. A missing executable or nonzero compiler exit raises `RuntimeError` with Typst's diagnostics.
== Troubleshooting

#docs-table(
  columns: (1.35fr, 1.65fr, 2fr),
  align: (left, left, left),
  table.header(text(weight: "bold")[Symptom], text(weight: "bold")[Likely cause], text(weight: "bold")[What to check]),
  [Typst reports “file not found” or “access denied”],
  [The fragment-relative path is wrong, or the image lies outside the Typst project root.],
  [Resolve the path from the generated `.typ` file, not the parent document. Compile from the intended tree or pass `typst compile --root <dir> …`.],

  [`.plot()` raises `ImportError`],
  [The optional plotting dependencies are absent.],
  [Install the project with its `images` extra. `.images()` does not need that extra; an `ImportError` there has another source.],

  [A selector raises `TypeError` or `ValueError` during rendering],
  [A deferred selector has an invalid source row, source column name, regex, structural row kind, or mask length.],
  [Check stable 0-based source row positions, exact original DataFrame column names, supported structural rows, regex matches, and one Boolean mask value per source row. Use the authoritative selector reference above.],

  [Markup prints literally or breaks output],
  [Escaping is enabled for raw markup, or disabled for untrusted plain text.],
  [Keep the default `escape=True` for ordinary values. Use `escape=False` only for trusted target-native markup; formatting-generated markup is tracked separately.],

  [Generated plots are missing from a saved table],
  [The saved fragment moved without its sibling asset directory, or a custom `assets=` path no longer resolves from it.],
  [Keep the fragment and its asset directory together, or use `.save(path, assets=...)` for an explicit placement. Direct `.render()` output embeds plots and needs no generated asset directory.],

  [A static image is missing],
  [Copy/embed resolves local inputs from Python's current working directory; reference mode resolves later from the saved fragment or served URL.],
  [Check `static_images`, the working directory used during `.save()`, and the emitted `assets=` location. For Typst, keep referenced files inside the compiler project root.],

  [HTML looks different from the compiled document],
  [HTML is a separate CSS/browser rendering, not a preview of Typst's paged layout.],
  [Use HTML for quick content and style checks; compile the Typst fragment for final widths, pagination, repeated headers, figure placement, and exact typography.],
)

When an error remains unclear, first render the smallest relevant backend directly (`table.render("typst")`, `"html"`, or `"ascii"`). This separates tytable's generated fragment from include paths, the browser/server base URL, and the surrounding Typst document.
== Coming from R tinytable

If you already use R's `tinytable`, tytable should feel familiar: create a table, then layer on formatting, styling, grouping, and themes. The main adjustments are Python method chaining, 0-based row indices, and selecting columns by name.

#docs-table(
  columns: (1fr, 1fr),
  align: (x, y) => (left, left).at(x),
  table.header(strong[R (`tinytable`)], strong[Python (`tytable`)]),
  [`tt(data)`],
  [`tt(df)` — Polars DataFrame],
  [`style_tt(x, ...)`],
  [`.style(...)`],
  [`format_tt(x, ...)`],
  [`.fmt(...)`],
  [`group_tt(x, ...)`],
  [`.group(...)`],
  [`theme_tt(x, ...)`],
  [`.theme_striped()` / `.theme_grid()` / other theme methods],
  [`print(x, "typst")`],
  [`.render("typst")`],
  [`save_tt(x, "out.typ")`],
  [`.save("out.typ")`],
  [`x %>% format(...) %>% ...`],
  [`.fmt(...).style(...)` — method chain],
  [`colnames(x) <- c(...)`],
  [`.set_name(name=[...])`],
  [1-based rows; 0 = colnames],
  [*0-based* data rows; `i="header"`],
  [column by integer position],
  [column by *name* (preferred)],
)
