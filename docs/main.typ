// tytable documentation
// Build:  make docs   (runs build_examples.py then typst compile)

#set page(
  paper: "a4",
  margin: (x: 2.4cm, y: 2.5cm),
  numbering: "1",
  number-align: center,
)

#set text(font: "New Computer Modern", size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.8em)

#set heading(numbering: "1.1")

// Code blocks: light panel, mono font.
#show raw: set text(font: "DejaVu Sans Mono")
#show raw.where(block: true): it => block(
  fill: luma(246),
  inset: 9pt,
  radius: 5pt,
  width: 100%,
  it,
)

// A helper to show the Python source of an example file.
#let source(path) = raw(read(path), block: true, lang: "python")

// A small "Source / Result" label.
#let tag(label) = text(size: 8.5pt, fill: luma(110), weight: "bold", tracking: 0.6pt)[#label]

// An API-reference entry: a bold, monospaced signature line.
#let api(sig) = block(spacing: 0.9em)[
  #set par(justify: false)
  #text(weight: "bold", raw(sig))
]

// Center every tytable figure and keep it from breaking awkwardly.
#show figure.where(kind: "tytable"): set align(center)

// ---------------------------------------------------------------------------
// Title page
// ---------------------------------------------------------------------------

#set page(numbering: none)

#align(center + horizon)[
  #block(height: 3cm)[]
  #text(size: 34pt, weight: "bold")[tytable]
  #v(0.4em)
  #text(size: 13pt, fill: luma(90))[Typst tables from Polars DataFrames]
  #v(2.2cm)
  #line(length: 32%, stroke: 0.6pt + luma(70))
  #v(0.6cm)
  #text(size: 11pt)[Documentation]
]

#pagebreak()

// ---------------------------------------------------------------------------
// Body
// ---------------------------------------------------------------------------

#set page(numbering: "1")
#counter(page).update(1)

= Introduction

#text(weight: "bold")[tytable] is a small Python library that turns Polars
DataFrames into Typst tables. It is inspired by R's
#link("https://github.com/vincentarelbundock/tinytable")[tinytable] package and
mirrors most of its styling power, while adding image and sparkline support plus
a Jupyter HTML preview.

The core idea: you record _intent_ (formatting, styling, grouping) by chaining
methods, and tytable replays it at render time into a Typst fragment you
`#import` straight into your reports.

== Install

```
pip install tytable
pip install tytable[images]   # for .plot() / .images() (matplotlib + numpy)
```

From GitHub with `uv`:
```
uv add git+https://github.com/EinMaulwurf/tytable.git
```

= Quickstart

#tag("SOURCE")
#source("examples/01_basic.py")

#tag("RESULT")
#v(0.4em)
#include "build/01_basic.typ"

The generated `.typ` file can be `#import`-ed into a Typst report and compiled
as part of the whole document. In Jupyter, let the `tt(...)` object be the last
line of a cell to see an HTML preview.

= Core concepts

== Row indexing is 0-based

`i=0` is the first _data_ row (the row *after* the column-name header). Use
`i="header"` for the column-name row, and negative integers for column-group
header rows (`-1` is the topmost level). Row-group separator rows are addressed
with `i="groupi"`, column-group rows with `i="groupj"`.

== Select columns by name

`j="Score"` is the preferred form; `j=0` selects the first column by position.
Both `i` and `j` also accept a #emph[list] to target several rows or columns in
one call: `j=["Q1 Rev", "Q1 Cost"]` or `j=[1, 2, 3, 4]`.

== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, and `.theme()` all return the table, so you
chain them. `.render()` and `.save()` are terminal.

== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Row indices always refer to the final,
visible table.

= Formatting

#emph[Format in polars first; use `.fmt()` for the rest.] Most formatting
(rounding, string ops, `fill_null`, percentages) is best done in polars before
passing the dataframe to `tt()`. `.fmt()` then covers the high-value cases
polars can't:

- `digits` — fixed decimal places (`num_fmt="decimal"`) or significant figures
  (`num_fmt="significant"`)
- `replace` — replace missing/null/NaN values with a string or a dict mapping
- `escape` — per-cell Typst escaping (on by default via `tt(escape=True)`)
- `fn` — custom column-wise transform

#tag("SOURCE")
#source("examples/02_format.py")

#tag("RESULT")
#v(0.4em)
#include "build/02_format.typ"

= Styling

Apply per-cell styling through selectors `i` (rows) and `j` (columns).
Supported properties: `bold`, `italic`, `underline`, `strikeout`, `monospace`,
`smallcaps`, `color`, `background`, `fontsize`, `align` (`l`/`c`/`r`), `alignv`
(`t`/`m`/`b`), `indent`, `colspan`, `rowspan`, and per-side borders (`line="tblr"`
in any combination, with `line_color` / `line_width`).

#tag("SOURCE")
#source("examples/03_style.py")

#tag("RESULT")
#v(0.4em)
#include "build/03_style.typ"

= Grouping

== Column groups

Spanning header rows. Pass a delimiter string to derive them from column names
(`.group(j="_")` splits each name on `_`), or a dict for explicit control:
`.group(j={"Group A": [0, 1], "Group B": [2, 3]})`.

== Row groups

Separator label rows inserted before a 0-based data row:
`.group(i={"Operational": 3})`.

#tag("SOURCE")
#source("examples/04_group.py")

#tag("RESULT")
#v(0.4em)
#include "build/04_group.typ"

= Themes

Built-in themes: `default` (booktab rules), `striped`, `grid`, `empty`, and
`rotate`. Pass a callable for a custom theme. The same data rendered under each
built-in:

#tag("SOURCE")
#source("examples/05_theme.py")

#tag("GALLERY — default")
#v(0.3em)
#include "build/05_theme_default.typ"

#tag("GALLERY — striped")
#v(0.3em)
#include "build/05_theme_striped.typ"

#tag("GALLERY — grid")
#v(0.3em)
#include "build/05_theme_grid.typ"

#tag("GALLERY — empty")
#v(0.3em)
#include "build/05_theme_empty.typ"

= Column widths

The `width` parameter of `tt()` accepts several forms: a single fraction spread
evenly, a per-column list of fractions, a Typst/HTML unit string, or `None` for
auto. You may mix all three in one list. Pass `width=1` for a #emph[full-width]
table — the fraction is split across columns so the table fills the available
content width (e.g. `width=0.5` covers half).

#tag("SOURCE")
#source("examples/06_widths.py")

#tag("RESULT")
#v(0.4em)
#include "build/06_widths.typ"

Pin the first column to a fixed Typst length and let the rest share the
remaining space with `1fr`, so the table spans the full content width while the
label column stays fixed:

#tag("SOURCE")
#source("examples/09_widths_fixed.py")

#tag("RESULT")
#v(0.4em)
#include "build/09_widths_fixed.typ"

= Images & sparklines

Supply your own plotting function `fun(values) -> matplotlib Figure`; tytable
handles PNG saving and path management. This example embeds a sparkline per row
and requires the `images` extra.

#tag("SOURCE")
#source("examples/07_images.py")

#tag("RESULT")
#v(0.4em)
#include "build/07_images.typ"

= Putting it together

A feature-rich table built without any image dependencies — combining explicit
column groups, a row-group separator, numeric formatting, a full-width layout,
and targeted styling. Note the list selectors: every numeric column is aligned
and formatted in a single call.

#tag("SOURCE")
#source("examples/08_full_report.py")

#tag("RESULT")
#v(0.4em)
#include "build/08_full_report.typ"

= API reference

Every chaining method returns the `TinyTable`, so they compose in a single
chain; `.render()` and `.save()` are terminal.

The selectors `i` (rows) and `j` (columns) are shared by `.style()`, `.fmt()`,
`.plot()`, and `.images()`:

- *rows* (`i`): `0` = first data row, `"header"` = column-name row, negative
  ints = column-group header rows (`-1` topmost), `"groupi"`/`"groupj"` = the
  row/column group separators, or a `list[int]`.
- *columns* (`j`): a name (`"Score"`), an integer position (`0`), a regex, or a
  `list` of names/positions — e.g. `j=["Q1 Rev", "Q1 Cost"]`.

#api("tt(data, *, caption=None, notes=None, width=None, gutter=2, colnames=True, escape=True, theme=\"default\", finalize=None)")
Create a `TinyTable` from a Polars DataFrame. `width=1` produces a full-width
table; it also takes a per-column list of fractions/units, a length string, or
`None` (auto). `gutter` is the Typst column gutter (pt when numeric, or a
string like `"0.1em"`); `None` suppresses it.

#api(".style(i=None, j=None, *, bold, italic, underline, strikeout, monospace, smallcaps, color, background, fontsize, align, alignv, indent, colspan, rowspan, line, line_color, line_width=0.1, line_trim, output=None)")
Apply cell styling via selectors. `line` is any combo of `t`/`b`/`l`/`r`;
`align` takes `l`/`c`/`r` and `alignv` takes `t`/`m`/`b`. Returns `self`.

#api(".fmt(i=None, j=None, *, digits=None, num_fmt=\"decimal\", replace=None, escape=False, fn=None, output=None)")
Apply value formatting: `digits` (with `num_fmt` of `"decimal"` or
`"significant"`), `replace` (a value or `{old: new}` mapping for nulls/NaNs),
or a custom column-wise transform `fn`. Returns `self`.

#api(".group(i=None, j=None)")
Add row groups (`i` as a `{label: row}` dict or a list) and column groups (`j`
as a `{label: [cols]}` dict or a delimiter string split out of the column
names). Returns `self`.

#api(".theme(name_or_callable=None)")
Apply a built-in theme (`default`, `striped`, `grid`, `empty`, `rotate`) or a
custom callable. Returns `self`.

#api(".plot(j, *, fun, data=None, height=1.0, color=\"black\", xlim=None, output=None)")
Embed a generated plot per cell. `fun(values, ...) -> matplotlib Figure` is
called once per row; tytable handles PNG saving and paths. Requires the
`images` extra. Returns `self`.

#api(".images(j, *, paths, height=1.0, output=None)")
Embed existing image files into the selected column. Requires the `images`
extra. Returns `self`.

#api(".render(output=\"typst\") -> str")
Render the table as a `"typst"` (default), `"html"`, or `"ascii"` string.
Terminal — does not return the table.

#api(".finalize(fn) -> self")
Register a post-render callback. `fn(rendered_string, output)` receives the
fully rendered string and the output format, and must return the (possibly
modified) string. Chainable; multiple callbacks run in registration order.

#api(".save(path, assets=None)")
Render and write to `path` (`.typ` or `.html`). `assets` overrides where image
files are written, relative to the output file. Terminal.

= Workflow: importing into a Typst report

Because you `#import` the generated `.typ` into a parent report and compile
elsewhere, image paths must resolve relative to your _Typst project root_ (where
`typst compile` runs). Make the assets location explicit:

```python
.save("build/tables/products.typ", assets="../assets/products")
```

Images then land in `build/assets/products/` and the `.typ` references
`../assets/products/...`, which resolves correctly from `build/tables/` when
compiled as part of the parent. Without an explicit `assets=`, images land in a
`tytable_assets/` folder next to the output file.

= Coming from R tinytable

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
  [`theme_tt(x, ...)`], [`.theme(...)` / `tt(theme=...)`],
  [`print(x, "typst")`], [`.render("typst")`],
  [`save_tt(x, "out.typ")`], [`.save("out.typ")`],
  [`x %>% format(...) %>% ...`], [`.fmt(...).style(...)` — method chain],
  [1-based rows; 0 = colnames], [*0-based* data rows; `i="header"`],
  [column by integer position], [column by *name* (preferred)],
)
