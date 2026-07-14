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
#let tag(label) = {
  v(0.7em)
  text(size: 8.5pt, fill: luma(110), weight: "bold", tracking: 0.6pt)[#label]
}

// An API-reference entry: a bold, monospaced signature line.
#let api(sig) = block(spacing: 0.9em)[
  #set par(justify: false)
  #text(weight: "bold", raw(sig))
]

// Center every tytable figure and keep it from breaking awkwardly.
#show figure.where(kind: "tytable"): set align(center)

#import "build/meta.typ": commit, build_date

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
  #v(0.4cm)
  #text(size: 9pt, fill: luma(140), tracking: 0.4pt)[#commit · built #build_date]
]

#pagebreak()

// ---------------------------------------------------------------------------
// Table of contents
// ---------------------------------------------------------------------------

#set page(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[Contents]
]
#v(0.8em)
#outline(title: none, indent: 1.5em, depth: 2)

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

Install from GitHub:
```
uv add git+https://github.com/EinMaulwurf/tytable.git
```

= Quickstart

#tag("SOURCE")
#source("examples/01_basic.py")

#tag("RESULT")
#v(0.12em)
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
Both `i` and `j` also accept a #emph[list] of strings or integers to target several rows or columns in
one call: `j=["Q1 Rev", "Q1 Cost"]`, `i=["header", "body"]`. `i` additionally
accepts Polars expressions, boolean series, and callables for data-driven
selection (see the *Styling* section).

== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, `.set_name()`, and `.theme()` all return the
table, so you chain them. `.render()` and `.save()` are terminal.

== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Row indices always refer to the final,
visible table.

= Renaming columns

`.set_name()` renames column headers for display without touching the
underlying Polars DataFrame — the original frame is never modified. This is
useful when the polars column names are machine-friendly identifiers but you
want human-readable headers in the rendered table, or when you need a header
that polars would reject as a column name (such as an empty string ``""`` or a
duplicate).

Two calling modes:

- *Per-column*: `.set_name(j, name=...)` renames the column(s) selected by `j`.
  `j` follows the same selector rules as `.style()` / `.fmt()` (name, integer
  position, or a list (or regex with `regex=True`, see `.style()`). `name` is a single `str` (applied to every
  matched column) or a `list[str]` with one entry per match.
- *Full-list replace*: `.set_name(name=[...])` (omit `j`) replaces every column
  header at once — the list length must equal the column count.

After renaming, subsequent `j` selectors use the _new_ display names; the old
polars column name no longer matches. The example starts from
`grp`, `val_1`, `val_2` and replaces them with `""`, `Revenue`, `Cost` — then
formats and aligns the renamed columns by their new names:

#tag("SOURCE")
#source("examples/15_set_name.py")

#tag("RESULT")
#v(0.12em)
#include "build/15_set_name.typ"

For one-off renames at construction time, `tt(df, colnames_override={old: new})`
does the same thing without a chained call.

= Formatting

Cell values can be formatted in three complementary ways. Pick whichever suits
the column, or mix them across columns in the same table.

== In polars

The most capable option: do everything #emph[before] passing the dataframe to
`tt()`. Polars expressions can round, cast numbers to strings, swap the decimal
delimiter, prepend a currency symbol, add thousands separators, and fill nulls —
anything polars can express, the table will render. Here revenue is rounded to
two decimals, formatted as USD with thousands separators, and nulls filled with
an em dash, all before `tt()` ever sees the data:

#tag("SOURCE")
#source("examples/11_format_polars.py")

#tag("RESULT")
#v(0.12em)
#include "build/11_format_polars.typ"

(Tytable's per-cell Typst escaping — `escape=True` by default — still applies to
whatever strings polars produces, so characters like `$` are escaped for you.)

== With `.fmt()`

For quick, in-table transforms that stay inside the `tt()` chain, without
reaching back into polars:

- `digits` — fixed decimal places (`num_fmt="decimal"`) or significant figures
  (`num_fmt="significant"`)
- `replace` — replace missing/null/NaN values with a string or a `{old: new}`
  mapping
- `escape` — per-cell Typst escaping (on by default via `tt(escape=True)`)

#tag("SOURCE")
#source("examples/02_format.py")

#tag("RESULT")
#v(0.12em)
#include "build/02_format.typ"

== With `.fmt(fn=...)`

For anything the built-ins don't cover, pass a callable to `fn`. It runs
#emph[column-wise]: tytable hands it the current string values of the selected
column (as a `list`) and expects a `list` of the same length back. This makes it
easy to implement transforms that depend on magnitude — for example,
abbreviating large numbers into a human-readable scale where `201818` becomes
"201.8 thousand" and `2729179` becomes "2.7 million":

#tag("SOURCE")
#source("examples/10_format_fn.py")

#tag("RESULT")
#v(0.12em)
#include "build/10_format_fn.typ"

= Styling

Apply per-cell styling through selectors `i` (rows) and `j` (columns).
Supported properties: `bold`, `italic`, `underline`, `strikeout`, `monospace`,
`smallcaps`, `color`, `background`, `fontsize`, `align` (`l`/`c`/`r`), `alignv`
(`t`/`m`/`b`), `indent`, `colspan`, `rowspan`, and per-side borders (`line="tblr"`
in any combination, with `line_color` / `line_width`).

Any number of these properties can be combined in a single `.style()` call when
they share the same `i`/`j` selector — e.g.
`*style(j="Score", align="r", background="#eee", bold=True)*` is one directive
rather than three separate calls. (Value formatting such as `digits` belongs to
`.fmt()`, a separate pipeline, and so always needs its own call.)

When `j` selects several columns, `align` and `alignv` also accept a
#emph[per-column string] with one shorthand character per selected column —
e.g. `align="llr"` left-aligns the first two and right-aligns the third.

#tag("SOURCE")
#source("examples/03_style.py")

#tag("RESULT")
#v(0.12em)
#include "build/03_style.typ"

== Caption and notes

The special selectors `i="caption"` and `i="notes"` style the table caption and
footnotes. These are not grid cells, so the styling is applied as inline text
markup — Typst `text(...)` / `#strong[...]` / `#smallcaps[...]`, or HTML `<span>`
plus `<b>` / `<i>` / … — rather than through the cell style grid. This mirrors
R tinytable's `style_tt(i="caption", …)` / `i="notes", …`.

Typst output is wrapped in a `figure` by default. Pass `label="product-scores"`
to attach `<product-scores>` to that figure, then reference the numbered table
with `@product-scores` in the surrounding Typst document. Pass `figure=False`
when an unnumbered table without figure semantics is more appropriate. Because
captions and numbered labels are figure features, combining `figure=False` with
either `caption` or `label` raises `ValueError`.

```python
(
    tt(
        df,
        caption="Product scores",
        label="product-scores",
        notes=["Source: Q3 report"],
    )
    .style(i="caption", bold=True, color="#c0392b", fontsize=1.2)
    .style(i="notes", italic=True, color="blue", align="c")
)
```

The text-level properties apply: `bold`, `italic`, `underline`, `strikeout`,
`monospace`, `smallcaps`, `color`, `fontsize` (plus `align`, `background`, and
`indent` for notes). Use `output=` to restrict styling to one backend, e.g.
`output=("typst",)`.

== List selectors

``i`` and ``j`` accept a list of strings as well as integers, so you can name
several rows or columns in one call without repeating yourself. A list-of-strings
``j`` selector like ``j=["Revenue", "Cost", "Growth %"]`` is self-documenting
and resilient to column reordering — no need to track integer positions.

The same works for ``i``: ``i=["header", "body"]`` styles the column-name row
and every data row in a single directive.

#tag("SOURCE")
#source("examples/13_list_selectors.py")

#tag("RESULT")
#v(0.12em)
#include "build/13_list_selectors.typ"

== Data-driven row selectors

Instead of hard-coding row numbers, select rows by value. ``i`` accepts three
dynamic forms evaluated against the original DataFrame at render time:

- A #emph[polars expression]: ``i=pl.col("Score") > 80``
- A #emph[boolean ``pl.Series``]: ``i=pl.Series("m", [True, False, True, False])``
- A #emph[Python callable]: ``i=lambda row: row["Grade"] == "D"``

All three work with ``.style()``, ``.fmt()``, ``.plot()``, and ``.images()``.
The expression or callable runs against the #emph[original] DataFrame (before
row-group insertion), so the column names you use are always the original ones.

#tag("SOURCE")
#source("examples/14_data_driven.py")

#tag("RESULT")
#v(0.12em)
#include "build/14_data_driven.typ"

= Grouping

== Column groups

Column groups add #emph[spanning header rows] above the regular column names, so
you can label clusters of related columns. The simplest way is to pass a
delimiter string: `.group(j="_")` splits every column name on that character and
turns the shared prefix into a group. In the example below the dataframe has
four columns named `Q1_revenue`, `Q1_cost`, `Q2_revenue`, and `Q2_cost`; the
underscore split yields two groups — `Q1` spanning the first two columns and
`Q2` spanning the last two. For full control you can instead pass a dict mapping
each label to its column positions, e.g.
`.group(j={"Group A": [0, 1], "Group B": [2, 3]})`.

== Row groups

Row groups insert a #emph[labelled separator row] before a given data row,
visually breaking the table into sections. Pass `i` as a `{label: row}` dict
where `row` is the 0-based data row the divider should precede. The example
calls `.group(i={"Division B": 1})` to place a "Division B" divider in front of
the second data row. That separator row is then addressable through the special
selector `i="groupi"` — used here to render its label bold on a light grey
background.

#tag("SOURCE")
#source("examples/04_group.py")

#tag("RESULT")
#v(0.12em)
#include "build/04_group.typ"

= Themes

Built-in themes: `default` (booktab rules), `striped`, `grid`, `empty`, and
`rotate`. The `resize` theme (see the dedicated section) scales a table to fit
the page. Pass a callable for a custom theme. The same data rendered under each
built-in:

#tag("SOURCE")
#source("examples/05_theme.py")

#tag("GALLERY — default")
#v(0.12em)
#include "build/05_theme_default.typ"

#tag("GALLERY — striped")
#v(0.12em)
#include "build/05_theme_striped.typ"

#tag("GALLERY — grid")
#v(0.12em)
#include "build/05_theme_grid.typ"

#tag("GALLERY — empty")
#v(0.12em)
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
#v(0.12em)
#include "build/06_widths.typ"

Pin the first column to a fixed Typst length and let the rest share the
remaining space with `1fr`, so the table spans the full content width while the
label column stays fixed:

#tag("SOURCE")
#source("examples/09_widths_fixed.py")

#tag("RESULT")
#v(0.12em)
#include "build/09_widths_fixed.typ"

= Resize

The `resize` theme scales a table to fit a target size, expressed as a fraction
of the available page area. It wraps the rendered fragment in a Typst
`#layout(size => …)` block that measures the table and rescales it by a uniform
factor. This is useful when a wide table would otherwise overflow the text
column.

Three knobs control the behaviour, exposed by the `theme_resize` callable:

- `width` — target width as a fraction of the page content width (`1` = full
  width). Used unless `height` is given.
- `height` — target height as a fraction of the page content height. When set,
  height drives the scaling and width follows proportionally.
- `direction` — `"down"` only shrinks oversized tables, `"up"` only expands
  undersized ones, `"both"` (default) always scales to the target.

```python
from tytable import tt
from tytable._themes import theme_resize

# Shrink only if wider than 95% of the page; leave smaller tables alone.
tt(df).theme(lambda t: theme_resize(t, width=0.95, direction="down"))

# Always scale to the full page width (the plain theme name does this).
tt(df, theme="resize")
```

#tag("SOURCE")
#source("examples/12_resize.py")

#tag("RESULT")
#v(0.12em)
#include "build/12_resize.typ"

= Images & sparklines

Supply your own plotting function `fun(values) -> matplotlib Figure`; tytable
handles PNG saving and path management. This example embeds a sparkline per row
and requires the `images` extra.

#tag("SOURCE")
#source("examples/07_images.py")

#tag("RESULT")
#v(0.12em)
#include "build/07_images.typ"

= Putting it together

A feature-rich table built without any image dependencies — combining explicit
column groups, a row-group separator, numeric formatting, a full-width layout,
and targeted styling. Note the list selectors: every numeric column is aligned
and formatted in a single call.

#tag("SOURCE")
#source("examples/08_full_report.py")

#tag("RESULT")
#v(0.12em)
#include "build/08_full_report.typ"

= API reference

Every chaining method returns the `TinyTable`, so they compose in a single
chain; `.render()` and `.save()` are terminal.

The selectors `i` (rows) and `j` (columns) are shared by `.style()`, `.fmt()`,
`.plot()`, and `.images()`:

- *rows* (`i`): `0` = first data row, `"header"` = column-name row, negative
  ints = column-group header rows (`-1` topmost), `"groupi"`/`"groupj"` = the
  row/column group separators, a `list` of any of the above, a Polars expression
  (`pl.col("Score") > 80`), a boolean `pl.Series`, or a callable
  ``lambda row: bool``.
- *columns* (`j`): a name (`"Score"`), an integer position (`0`), or a
  `list` of names/positions — e.g. `j=["Q1 Rev", "Q1 Cost"]`. Set `regex=True`
  to treat string selectors as regex patterns.

`.style()` additionally accepts `i="caption"` and `i="notes"` to style the table
caption and footnotes as inline text (see the *Caption and notes* section).

#api("tt(data, *, figure=True, caption=None, label=None, notes=None, width=None, gutter=2, colnames=True, escape=True, theme=\"default\", finalize=None)")
Create a `TinyTable` from a Polars DataFrame. `width=1` produces a full-width
table; it also takes a per-column list of fractions/units, a length string, or
`None` (auto). Typst output uses a figure by default; `figure=False` emits an
unnumbered table, while `label="name"` labels the figure for cross-references.
Captions and labels require `figure=True`. `gutter` is the Typst column gutter
(pt when numeric, or a string like `"0.1em"`); `None` suppresses it.

#api(".style(i=None, j=None, *, bold, italic, underline, strikeout, monospace, smallcaps, color, background, fontsize, align, alignv, indent, colspan, rowspan, line, line_color, line_width=0.1, line_trim, output=None)")
Apply cell styling via selectors. `line` is any combo of `t`/`b`/`l`/`r`;
`align` takes `l`/`c`/`r` and `alignv` takes `t`/`m`/`b`; with multi-column `j`,
a per-column string like `align="llr"` is accepted. Returns `self`.

#api(".fmt(i=None, j=None, *, digits=None, num_fmt=\"decimal\", replace=None, escape=False, fn=None, output=None)")
Apply value formatting: `digits` (with `num_fmt` of `"decimal"` or
`"significant"`), `replace` (a value or `{old: new}` mapping for nulls/NaNs),
or a custom column-wise transform `fn`. Returns `self`.

#api(".group(i=None, j=None)")
Add row groups (`i` as a `{label: row}` dict or a list) and column groups (`j`
as a `{label: [cols]}` dict or a delimiter string split out of the column
names). Returns `self`.

#api(".set_name(j=None, *, name)")
Rename column headers for display only (the underlying DataFrame is untouched).
Per-column: `.set_name(j, name="X")` (or `name=[...]` matching the selected
count). Full-list replace: `.set_name(name=[...])` with `j` omitted — length
must equal the column count. Subsequent `j` selectors use the new names.
Returns `self`.

#api(".theme(name_or_callable=None)")
Apply a built-in theme (`default`, `striped`, `grid`, `empty`, `rotate`,
`resize`) or a custom callable. Returns `self`. For parameterized themes such
as `resize`, pass a callable: `.theme(lambda t: theme_resize(t, width=0.9, direction="down"))`.

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
  [`colnames(x) <- c(...)`], [`.set_name(name=[...])`],
  [1-based rows; 0 = colnames], [*0-based* data rows; `i="header"`],
  [column by integer position], [column by *name* (preferred)],
)
