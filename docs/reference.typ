#import "_common.typ": api, api_signatures

#pagebreak()

= — Reference <api-reference>

Use this part for task-based lookup. It collects the complete selector rules,
method signatures, error contracts, and migration notes.

== Task-oriented API reference

Start here when you know the task but not the method. Methods marked
*chainable* mutate the `TyTable` and return `self`; output methods are terminal.

#table(
  columns: (1.15fr, 1.2fr, 2.65fr),
  align: (left, left, left),
  inset: 6pt,
  stroke: (x, y) => if y == 0 { (bottom: 0.7pt + rgb("#153243")) } else { none },
  table.header(text(weight: "bold")[Task], text(weight: "bold")[Use], text(weight: "bold")[Result]),
  [Create], [`tt(...)`], [`TyTable`],
  [Style cells], [`.style(...)`], [chainable],
  [Format values], [`.fmt(...)`], [chainable],
  [Group rows/columns], [`.group(...)`], [chainable],
  [Rename headers], [`.set_name(...)`], [chainable],
  [Add a built-in theme], [`.theme_striped()` / `.theme_resize(...)`], [chainable],
  [Apply a custom theme], [`.theme(fn)`], [chainable],
  [Add plots/images], [`.plot(...)` / `.images(...)`], [chainable],
  [Post-process output], [`.finalize(...)`], [chainable],
  [Get a string], [`.render(...)`], [`str` (terminal)],
  [Write a file], [`.save(...)`], [`None` (terminal)],
)

=== Authoritative selector reference

`.style()`, `.fmt()`, `.plot()`, and `.images()` share `i` and `j`;
`.style()` and `.fmt()` additionally accept the cell-level `where` selector.
`.set_name()` shares `j`. With `i=None`, `.style()` targets every grid row
(column-group headers, the column-name header when shown, and the complete
visible body), while `.fmt()`, `.plot()`, and `.images()` target the body only.
With `j=None`, every column is selected (`.plot()` and `.images()` require an
explicit `j`; `.set_name()` instead enters full-list replacement mode).

#table(
  columns: (0.8fr, 1.45fr, 2.75fr),
  align: (left, left, left),
  inset: 6pt,
  fill: (x, y) => if y > 0 and calc.odd(y) { rgb("#f4f7f8") } else { none },
  table.header(text(weight: "bold")[Selector], text(weight: "bold")[Example], text(weight: "bold")[Meaning]),
  [`i`], [`0`, `2`, `[0, 2]`], [0-based final visible body row(s)],
  [`i`], [`"header"`, `"body"`], [column names or all table-body rows],
  [`i`], [`"all"`], [all header rows and the complete visible body],
  [`i`], [`"groupi"`, `"~groupi"`], [row-group rows or genuine data rows only],
  [`i`], [`"groupj"`], [column-group header rows],
  [`i`], [`-1`, `-2`], [column-group rows, from innermost upward],
  [`i`], [`pl.col("Score") > 80`], [Polars expression evaluated on source data],
  [`i`], [`pl.Series(...)`], [boolean mask with one value per source row],
  [`i`], [`lambda row: ...`], [predicate receiving a row dictionary],
  [`j`], [`"Score"`, `0`], [column name (preferred) or position],
  [`j`], [`["Revenue", "Cost"]`], [several columns in one directive],
  [`where`], [`cs.numeric() > 100`], [true body cells in `.style()` / `.fmt()`],
)

Non-negative integer `i` values range from zero through the final visible body
length minus one. Row-group separators count as visible body rows, so an
integer recorded before or after `.group()` addresses the same final
coordinate. Negative integers address only column-group headers: `-1` is the
innermost, and the most negative valid value is the outermost. `"header"` is
empty when column names are hidden; `"groupj"` and negative selectors are
empty or invalid when no column-group rows exist. Lists/tuples may mix integer
and string row selectors. `.style()` also accepts `i="caption"` and
`i="notes"`; these non-grid targets allow only their documented text-oriented
properties.

Data-driven `i` forms have a different coordinate system: a Polars expression,
boolean list/tuple, boolean `pl.Series`, or `callable(row_dict) -> bool` is
evaluated against the original DataFrame. Masks must be Boolean and have
exactly one entry per source row; a boolean mask cannot mix booleans with
integer selectors. Matching source rows are mapped around inserted row-group
separators. Thus use an integer for a final visible row, or a predicate/mask
when the target is an original data row. `where` is also evaluated against the
original DataFrame; it must return Boolean columns with original source-column
names and the source row count. Its true cells are intersected with `i` and
`j`, and it cannot target synthetic headers, group rows, captions, or notes.

Integer `j` values range from zero through the column count minus one. Exact
string names are case-sensitive and select the first matching display name.
This matters because `.set_name()` permits duplicates: use an integer to select
a later duplicate, or `regex=True` to match all duplicates. Column selectors
are resolved lazily against the table's current display names, so a rename also
affects directives recorded earlier; `where` expressions continue to use the
original DataFrame names. A list preserves its requested order and may repeat
an exact selector.

With `regex=True`, every string element of `j` is a Python `re.search` pattern,
not a full match. Each pattern is limited to 500 characters and must match at
least one column; invalid patterns and no-match patterns raise `ValueError`.
Matches from a regex list are de-duplicated in first-match order. Integer
elements keep their normal meaning. Regex applies only to `j`, not `i` or
`where`.

=== Creating a table

#api("Create", api_signatures.at("tt"))

`data` is a Polars `DataFrame` and is cloned on construction. The constructor
options fall into four groups:

#table(
  columns: (1.05fr, 1.9fr, 2.05fr),
  align: (left, left, left),
  inset: 5pt,
  table.header(text(weight: "bold")[Concern], text(weight: "bold")[Options], text(weight: "bold")[Notes]),
  [Figure], [`figure`, `caption`, `label`, `notes`], [captions and labels require `figure=True`],
  [Layout], [`width`, `height`, `gutter`], [`width=1` fills the line; lists set each column],
  [Headers], [`colnames`, `colnames_override`], [show and rename display headers],
  [Values], [`escape`], [global safe-markup policy],
  [Behaviour], [`finalize`], [initial output callback],
  [Reserved], [`rownames`], [present for parity; not implemented],
)

`width` accepts a fraction, a Typst length string, or one entry per column
(fractions, strings such as `"3cm"` / `"1fr"`, and `None` may be mixed).
`gutter` accepts points as a number, a unit string, or `None`. The constructor's
`digits` parameter is retained for compatibility; use `.fmt(digits=...)` to
configure numeric formatting. A note is a string or a `NoteDict`, exported from
`tytable`. Its optional keys are `text` (footer text), `marker` (an explicit
string or `None`), `i` (row selector), and `j` (column selector):

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

The annotation makes these keys and selector types discoverable to type checkers
and IDEs. When `marker` is absent, a note with `i` or `j` is numbered
automatically; an untargeted note remains unmarked.

`TyTable(...)` has the same constructor options, but application code should
normally construct with `tt(...)` and use `TyTable` for annotations.

=== Formatting and structure

#api("Style", api_signatures.at("style"))

Combines any properties sharing the same selectors. `where` accepts a Polars
expression for cell-level selection. `align` uses `l`/`c`/`r`,
`alignv` uses `t`/`m`/`b`, `rotate` is degrees, and `line` is any combination
of `t`/`b`/`l`/`r`. With several columns, `align="llr"` assigns one alignment
per column. `fontsize`, `indent`, and `line_width` are in `em`. `output` can
restrict a directive to a tuple such as `("typst",)`.

#api("Format", api_signatures.at("fmt"))

Transforms values in this order: `digits`, `fn`, `replace`, `linebreak`,
`math`, then `escape`.
`where` restricts all transforms in the directive to individual true body cells.
`digits` is either `None` (no numeric formatting) or a non-negative integer;
booleans are rejected even though Python treats them as integers. `num_fmt` is
`"decimal"`, `"significant"`, or `"scientific"`. Decimal formatting uses
`digits` places after the decimal point, significant formatting uses that many
significant figures, and scientific formatting uses that many places after the
mantissa's decimal point. Both integer and floating-point values are formatted;
booleans, nulls, and non-numeric values are left unchanged. Scientific notation
uses target-native Typst/HTML markup and a plain-text form in ASCII.

`digits`, `num_fmt`, and whether `fn` is callable are validated immediately when
`.fmt()` is called. Selectors are resolved and `fn` results are validated during
rendering. `fn` receives each selected column as `list[str]` after numeric
formatting and must return a non-string sequence of the same length. `replace`
then may blank missing values, supply a replacement string, or map old values to
new ones. `linebreak` is a literal marker replaced for Typst and HTML output.
`math=True` wraps Typst values in math delimiters without changing HTML or ASCII.

#api("Group", api_signatures.at("group"))

For row groups, pass `{label: row}` or a list with one group value per data row.
For spanning column headers, pass `{label: [columns]}` as `j`, or pass a literal
string as `delimiter` to split every column name. `j` and `delimiter` are
mutually exclusive.

#api("Rename display headers", api_signatures.at("set_name"))

With `j`, `name` is one display name or a list matching the selected columns.
Without `j`, pass the complete list of display names. The DataFrame remains
unchanged; later `j` selectors use the new display names.

#api("Custom theme", api_signatures.at("theme"))

`fn` is a callable `theme(table) -> TyTable | None`. Built-in themes use the
typed methods below; they stack on the implicit default theme.

#api("Add stripes", api_signatures.at("theme_striped"))

#api("Add a grid", api_signatures.at("theme_grid"))

#api("Reset styling", api_signatures.at("theme_empty"))

This reset is destructive and order-sensitive. Call it immediately after
`tt(...)`; constructor-level figure, row-height, and gutter settings survive.

#api("Rotate", api_signatures.at("theme_rotate"))

With no selectors, rotates the whole table. Pass `i` and/or `j` to rotate
selected cell content instead.

#api("Resize", api_signatures.at("theme_resize"))

Scales Typst output by width or height. `direction` is `"down"`, `"up"`, or
`"both"`.

#api("Span pages", api_signatures.at("theme_multipage"))

Makes the Typst figure breakable. Header and column-group rows repeat on each
page unless `repeat_headers=False`.

=== Plots and images

Only generated plots require the optional `images` extra. `.images()` only emits
references to existing files and has no optional Python dependencies. Media is
materialized when the table renders or saves, not when the directive is recorded.

For both methods, tytable resolves `i` and `j` at render time and walks the
selection row-major: each resolved row in order, then each resolved column in
order. `.images(paths=...)` always requires exactly one path per selected cell.
When `.plot(data=...)` is supplied, it likewise requires exactly one item per
selected cell; without `data`, the callback receives each selected cell's typed
DataFrame value. Empty selections therefore require an empty supplied list.
Too few or too many items raise `ValueError` before plotting dependencies are
loaded or callbacks run.

#api("Generate plots", api_signatures.at("plot"))

`j` and `fun` are required. The callable receives the typed cell value (or the
matching `data` entry) and returns a Matplotlib `Figure` or `plotnine` plot. Pixel
dimensions control PNG generation for both backends and override a returned
Matplotlib figure's canvas size; `height` independently controls the displayed
cell size. `color` and `xlim` are inspected independently: each keyword is
forwarded only if the callback declares it or accepts `**kwargs`. Plot callbacks
and PNG generation run during `.render()` / `.save()`; non-portable rendering
writes an asset for every selected cell, while Typst portable mode creates a
temporary PNG and embeds it in the returned fragment.

#api("Embed files", api_signatures.at("images"))

`j` and `paths` are required. Paths are assigned row-major across selected
cells. Tytable neither checks nor copies these files; paths are emitted as supplied
(with path separators normalized). A relative path resolves from the saved `.typ`
or `.html` fragment. The `assets=` argument does not change static image paths.
Rendering only materializes backend image markup; it does not open or verify the
referenced file.

=== Rendering and output

#api("Post-process", api_signatures.at("finalize"))

Registers `fn(rendered: str, output: str) -> str`. Callbacks run in registration
order after any renderer and are useful for narrowly scoped integration markup.

#api("Render string", api_signatures.at("render"))

`output` is `"typst"`, `"html"`, or `"ascii"`. Rendering resolves all recorded
intent and runs finalizers. The same table can be rendered more than once. See
#link(<alternative-backends>)[Alternative backends] for HTML and ASCII usage,
including terminal previews with `print(table)`. By default, a direct render of a
table with `.plot()` writes generated PNGs to `tytable_assets/` under the current
working directory and emits `tytable_assets/<filename>`. Because a returned string
has no file location, saving it elsewhere yourself also requires moving the assets or
adjusting the references. Rendering static `.images()` references does not touch the
referenced files. Typst portable mode embeds generated plots instead of retaining PNGs.

An unsupported `output` raises `NotImplementedError`. Most selectors are
recorded first, so invalid selector types, positions, mask lengths, regexes, and
missing columns raise `TypeError` or `ValueError` during `.render()`; grouping
specifications and the selectors used by `.set_name()` are validated when those
methods are called. Formatter option errors are raised by `.fmt()`, while an
invalid formatter result raises `TypeError` or `ValueError` during rendering.
Only a `.plot()` directive can raise the optional-dependency `ImportError`.
A plot callback exception is wrapped in `RuntimeError` with directive and cell
context; an unsupported callback return is `TypeError`; and failures to create
or write generated assets raise `OSError` with their destination. Exceptions
from finalizer callbacks propagate unchanged.

#api("Save file", api_signatures.at("save"))

Creates parent directories and infers HTML from `.html` / `.htm`; other
suffixes produce Typst. `assets` controls generated `.plot()` PNGs only. A relative
value is resolved from the output file's directory and is also emitted in the
fragment; the default is a sibling `tytable_assets/` directory. `.save()` stores
this destination on the table. Later direct `.render()` calls on the same object
continue to write there and emit the retained relative path; another `.save()`
replaces it. Use a fresh table when independent render destinations are required.
`save()` can additionally raise `OSError` while creating the destination directory
or writing the table file. Render-time selector, formatter, plot, and asset errors
otherwise have the same contracts described for `.render()` above.


== Troubleshooting

#table(
  columns: (1.35fr, 1.65fr, 2fr),
  align: (left, left, left),
  inset: 5pt,
  fill: (x, y) => if y > 0 and calc.odd(y) { rgb("#f4f7f8") } else { none },
  table.header(
    text(weight: "bold")[Symptom],
    text(weight: "bold")[Likely cause],
    text(weight: "bold")[What to check],
  ),
  [Typst reports “file not found” or “access denied”],
  [The fragment-relative path is wrong, or the image lies outside the Typst project root.],
  [Resolve the path from the generated `.typ` file, not the parent document. Compile from the intended tree or pass `typst compile --root <dir> …`.],
  [`.plot()` raises `ImportError`],
  [The optional plotting dependencies are absent.],
  [Install the project with its `images` extra. `.images()` does not need that extra; an `ImportError` there has another source.],
  [A selector raises `TypeError` or `ValueError` during rendering],
  [Selectors are deferred and no longer match the final names, rows, or source-mask length.],
  [Check 0-based final visible row positions, exact display column names, regex matches, and one Boolean mask value per source row. Use the authoritative selector reference above.],
  [Markup prints literally or breaks output],
  [Escaping is enabled for raw markup, or disabled for untrusted plain text.],
  [Keep the default `escape=True` for ordinary values. Use `escape=False` only for trusted target-native markup; formatting-generated markup is tracked separately.],
  [Generated plots are missing or appear in an old directory],
  [Direct `.render()` uses `./tytable_assets/`, while a previous `.save()` retains its asset destination on the table.],
  [Prefer `.save(path, assets=...)` for explicit placement. Use a fresh table for independent destinations, or move assets and update references when persisting a rendered string yourself.],
  [A static image is missing],
  [`.images()` preserves the supplied path and does not verify or copy the file.],
  [Make the path relative to the saved fragment (or served HTML URL), and ensure the file is inside the Typst project root. `assets=` affects generated plots only.],
  [HTML looks different from the compiled document],
  [HTML is a separate CSS/browser rendering, not a preview of Typst's paged layout.],
  [Use HTML for quick content and style checks; compile the Typst fragment for final widths, pagination, repeated headers, figure placement, and exact typography.],
)

When an error remains unclear, first render the smallest relevant backend
directly (`table.render("typst")`, `"html"`, or `"ascii"`). This separates
tytable's generated fragment from include paths, the browser/server base URL,
and the surrounding Typst document.


== Coming from R tinytable

If you already use R's `tinytable`, tytable should feel familiar: create a table,
then layer on formatting, styling, grouping, and themes. The main adjustments are
Python method chaining, 0-based row indices, and selecting columns by name.

#table(
  columns: (1fr, 1fr),
  align: (x, y) => (left, left).at(x),
  table.hline(y: 0, stroke: 0.08em + black),
  table.hline(y: 1, stroke: 0.05em + black),
  table.hline(stroke: 0.08em + black),
  table.header(strong[R (`tinytable`)], strong[Python (`tytable`)]),
  [`tt(data)`], [`tt(df)` — Polars DataFrame],
  [`style_tt(x, ...)`], [`.style(...)`],
  [`format_tt(x, ...)`], [`.fmt(...)`],
  [`group_tt(x, ...)`], [`.group(...)`],
  [`theme_tt(x, ...)`], [`.theme_striped()` / `.theme_grid()` / other theme methods],
  [`print(x, "typst")`], [`.render("typst")`],
  [`save_tt(x, "out.typ")`], [`.save("out.typ")`],
  [`x %>% format(...) %>% ...`], [`.fmt(...).style(...)` — method chain],
  [`colnames(x) <- c(...)`], [`.set_name(name=[...])`],
  [1-based rows; 0 = colnames], [*0-based* data rows; `i="header"`],
  [column by integer position], [column by *name* (preferred)],
)
