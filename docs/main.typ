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

// A scannable API-reference card: task label followed by a Python signature.
#let api(title, sig) = block(
  width: 100%,
  breakable: false,
  fill: rgb("#eef5f6"),
  inset: (x: 10pt, y: 8pt),
  radius: 5pt,
  spacing: 0.8em,
)[
  #set par(justify: false)
  #text(size: 8.5pt, weight: "bold", fill: rgb("#087e8b"), tracking: 0.4pt)[
    #upper(title)
  ]
  #v(0.35em)
  #raw(sig, block: true, lang: "python")
]

// Center every tytable figure and keep it from breaking awkwardly.
#show figure.where(kind: "tytable"): set align(center)

#import "build/meta.typ": build_date, commit, version
#let api_signatures = json("build/api.json")

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
  #text(size: 10pt, fill: luma(110))[Version #version]
  #v(0.25cm)
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
mirrors most of its styling power, including image and sparkline support plus
a Jupyter HTML preview.

== What is Typst?

Typst is a markup-based typesetting system: you write a plain-text `.typ` file
containing prose, headings, equations, figures, and layout instructions, then
compile it into a PDF. It fills a role similar to LaTeX, with a compact modern
syntax and a fast compiler. A tiny Typst document looks like this:

```typst
#set page(paper: "a4")
= Results

The experiment completed successfully.
```

Typst is excellent at page layout, but an analysis usually starts somewhere
else: in Python, with a Polars DataFrame produced by a query, aggregation, or
model. Rewriting that data by hand as Typst table cells is repetitive and
error-prone. It also leaves you to solve escaping, number formatting, spanning
headers, footnotes, image paths, and consistent styling over and over.

== Why tytable exists

Tytable is the bridge between those two jobs:

#table(
  columns: (1fr, 0.25fr, 1fr, 0.25fr, 1fr),
  align: center + horizon,
  inset: 7pt,
  stroke: none,
  [*Polars*\ data and computation], [→], [*tytable*\ table intent], [→], [*Typst*\ document and PDF],
)

Python continues to own the data. Typst continues to own the document. Tytable
only describes how the DataFrame becomes a table: format these values, style
those cells, add these groups, and emit a self-contained Typst fragment. The
same object can also render HTML for a notebook preview or ASCII for a terminal.

The core idea is to record _intent_ by chaining methods. Tytable replays that
intent at render time, after the final table shape is known. This keeps the
Python code readable and avoids generating Typst markup by hand.

Install the latest release from
#link("https://pypi.org/project/tytable/")[PyPI]:

```
uv add tytable
```

The equivalent pip command is `pip install tytable`. Install the optional
images extra when generating plots or sparklines. Existing image files can be
embedded without additional Python dependencies:

```
uv add "tytable[images]"
```

Tytable-generated `.typ` fragments require *Typst 0.11.0 or newer* to compile.
The published documentation PDF is built with Typst 0.15.0.

#pagebreak()

= Start here: your first table

Begin with a Polars DataFrame and pass it to `tt`. That is enough to make a
table—there is no style configuration to learn first.

#tag("SOURCE")
#source("examples/01_basic.py")

#tag("RESULT")
#v(0.12em)
#include "build/01_basic.typ"

In Jupyter, the last two lines can simply be:

```python
table = tt(data)
table
```

Jupyter shows an HTML preview. In a script, `.save("catalog.typ")` writes the
Typst fragment shown above. Saving does not compile a PDF; install the
#link("https://typst.app/open-source/")[Typst CLI] before using `typst compile`
locally.

== Make one column easier to read

Now add one formatting decision. Column names are used directly, so this reads
as “show Price with two decimal places”:

```python
table = tt(data).fmt(j="Price", digits=2)
```

== Add one visual cue

Styling is another chained instruction. A header treatment is a useful first
one because it does not depend on the number of data rows:

```python
table = (
    tt(data)
    .fmt(j="Price", digits=2)
    .style(i="header", bold=True, background="#17324d", color="white")
)
```

== Put it in a report

Add figure metadata when the table becomes part of a larger document, then
save it:

#tag("SOURCE")
#source("examples/01_report_ready.py")

#tag("RESULT — ready for the report")
#v(0.12em)
#include "build/tables/catalog.typ"

The generated file can be `#include`-ed in a Typst report. Refer to the
numbered figure there with `@product-catalog`.

== The storyline from here

The rest of this guide grows that first table one concern at a time:

1. understand rows, columns, and chaining;
2. format values and rename display headers;
3. add styling, groups, themes, and layout;
4. embed plots and assemble a complete report table;
5. turn the same chain into a reusable, typed Python component;
6. use the task-oriented API reference to find the method for a job.

= Core concepts

Four conventions make tytable chains predictable before you begin combining
formatting, styling, and grouping directives.

== Row selectors are semantic

`i=0` is the first source DataFrame row. Non-negative integers keep that
meaning even when row-group separators are inserted before them. Omitting `i`,
or writing `i="data"` explicitly, selects every genuine source-data row. Use
`i="header"` for the column-name row, `i="groupi"` for row-group separators,
`i="groupj"` for all column-group rows, and `i="all"` for the complete grid.
Negative public row indices are not supported.

The selector vocabulary is shared, but each operation accepts only rows whose
content it can represent. `.style()` supports every grid row. `.fmt()` and
targeted notes support data rows, row-group separators, and the column-name
header. `.plot()` and `.images()` support data and row-group rows. Selecting an
unsupported row kind raises a targeted error during rendering instead of being
silently ignored.

== Select columns by name

`j="Score"` is the preferred form; `j=0` selects the first column by position.
Both `i` and `j` also accept a #emph[list] of strings or integers to target several rows or columns in
one call: `j=["Q1 Rev", "Q1 Cost"]`, `i=["header", "data"]`. `i` additionally
accepts Polars expressions, boolean series, and callables for data-driven
selection (see the *Styling* section).

`.fmt()` and `.style()` use the intersection of `i` and `j`, so combining them
targets individual cells—for example, `.fmt(i=1, j="Score", digits=1)` formats
only the `Score` cell in the second data row, and `.style(i=1, j="Score",
bold=True)` styles only that cell.

== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, `.set_name()`, the `.theme_*()` methods, and
the named layout operations all return the table, so you chain them.
`.render()` and `.save()` are terminal.

== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Integer row selectors always refer to
stable, 0-based source DataFrame rows.

= Renaming columns

`.set_name()` renames column headers for display without touching the
underlying Polars `DataFrame` — the original frame is never modified. This is
useful when the Polars column names are machine-friendly identifiers but you
want human-readable headers in the rendered table, or when you need a header
that Polars would reject as a column name (such as an empty string `""` or a
duplicate).

Two calling modes:

- *Per-column*: `.set_name(j, name=...)` renames the column(s) selected by `j`.
  `j` follows the same selector rules as `.style()` / `.fmt()` (name, integer
  position, a list, or a regex with `regex=True`; see `.style()`). `name` is a
  single `str` (applied to every matched column) or a `list[str]` with one entry
  per match.
- *Full-list replace*: `.set_name(name=[...])` (omit `j`) replaces every column
  header at once — the list length must equal the column count.

Every `j` selector continues to use the original Polars column names, whether
the directive was recorded before or after the rename. Display labels are
presentation only and never become selectors. This keeps duplicate and empty
labels unambiguous: the example displays `""`, `Revenue`, and `Cost`, then
formats those columns using the source names `val_1` and `val_2`. Their
alignment continues to follow the source-column numeric dtypes:

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

== In Polars

The most capable option: do everything #emph[before] passing the dataframe to
`tt()`. Polars expressions can round, cast numbers to strings, swap the decimal
delimiter, prepend a currency symbol, add thousands separators, and fill nulls —
anything Polars can express, the table will render. Here revenue is rounded to
two decimals, formatted as USD with thousands separators, and nulls filled with
an em dash, all before `tt()` ever sees the data:

Because that Polars expression converts `Revenue` to a string column, the
example explicitly restores right alignment with `.style(align="r")`. In
contrast, `.fmt()` preserves the source dtype and therefore needs no alignment
style for numeric columns.

#tag("SOURCE")
#source("examples/11_format_polars.py")

#tag("RESULT")
#v(0.12em)
#include "build/11_format_polars.typ"

(Tytable's per-cell Typst escaping — `escape=True` by default — still applies to
whatever strings Polars produces, so characters like `$` are escaped for you.)

== With `.fmt()`

For quick, in-table transforms that stay inside the `tt()` chain, without
reaching back into polars:

- `digits` — fixed decimal places (`num_fmt="decimal"`), significant figures
  (`num_fmt="significant"`), or typeset scientific notation
  (`num_fmt="scientific"`)
- `replace` — replace missing/null/NaN values with a string or a `{old: new}`
  mapping
- `linebreak` — choose a literal input marker to replace with a native line
  break. For example, `linebreak="\n"` translates newline characters to a
  single `\` in Typst or `<br>` in HTML; use another marker such as `"|"` when
  that is more convenient for the source data
- `math` — typeset selected values as Typst equations
- `escape` — per-cell Typst escaping (on by default via `tt(escape=True)`)

Formatting text and equations does not require disabling safe escaping. This
example treats `Formula` as Typst math and uses `|` inside `Detail` to mark
where a native line break should appear:

```python
df = pl.DataFrame({
    "Formula": ["x^2 + y^2", "sum_(i=1)^n i"],
    "Detail": ["first line|second line", "one line"],
})

table = (
    tt(df)
    .fmt(j="Formula", math=True)
    .fmt(j="Detail", linebreak="|")
)
```

Math mode is Typst-specific; HTML and ASCII retain the original value.
Line-break replacement targets Typst and HTML, while ASCII retains the marker.

The larger example below puts the built-ins side by side: decimal, significant,
and scientific numbers, missing-value replacement, and Typst math. Each
`.fmt()` call targets the column that needs that particular transformation.

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
`"201.8 thousand"` and `2729179` becomes `"2.7 million"`:

#tag("SOURCE")
#source("examples/10_format_fn.py")

#tag("RESULT")
#v(0.12em)
#include "build/10_format_fn.typ"

The #link("https://mizani.readthedocs.io/en/stable/labels.html")[Mizani]
package is the closest Python equivalent to R's `scales`. Its vectorized label
callables cover currencies, percentages, scientific notation, dates, and more.
Because `.fmt(fn=...)` supplies strings, a small typed adapter converts the
values to numbers first. A following `.fmt(escape=True)` safely escapes symbols
introduced by the external formatter when required by the output backend, such
as `$` in Typst:

#tag("SOURCE")
#source("examples/10_mizani.py")

#tag("RESULT")
#v(0.12em)
#include "build/10_mizani.typ"

Mizani is an optional development dependency used for this documentation
example; it is not installed with tytable at runtime.

= Styling

Styling directives control the appearance of cells and table-adjacent text
without changing the underlying values.

By default, text columns and their headers are left-aligned, while columns with
Polars numeric dtypes and their headers are right-aligned. Alignment is inferred
from the source dtype before `.fmt()` changes the displayed text, so formatted
numbers, replacement marks, currencies, and percentages stay aligned. An explicit
`.style(align=...)` directive takes precedence. Column-group headers are centered.

== Styling cells

Apply per-cell styling through selectors `i` (rows) and `j` (columns).
Supported properties: `bold`, `italic`, `underline`, `strikeout`, `monospace`,
`smallcaps`, `color`, `background`, `fontsize`, `align` (`l`/`c`/`r`), `alignv`
(`t`/`m`/`b`), `indent`, `colspan`, `rowspan`, and per-side borders (`line="tblr"`
in any combination, with `line_color` / `line_width`).

Any number of these properties can be combined in a single `.style()` call when
they share the same selectors — e.g.
`style(j="Score", align="c", background="#eee", bold=True)` is one directive
rather than three separate calls. (Value formatting such as `digits` belongs to
`.fmt()`, a separate pipeline, and so always needs its own call.)

Omit `i` (or use `i="data"`) when a style should apply to every source-data row
while leaving structural rows alone. The example below uses it to draw the left and right
borders around the body; its header has a separate style.

When `j` selects several columns, `align` and `alignv` also accept a
#emph[per-column string] with one shorthand character per selected column —
e.g. `align="llr"` left-aligns the first two and right-aligns the third.

#tag("SOURCE")
#source("examples/03_style.py")

#tag("RESULT")
#v(0.12em)
#include "build/03_style.typ"

== Color values and backend scope

`color`, `background`, and `line_color` accept case-insensitive bundled CSS
color names, with both `gray` and `grey` spellings where CSS defines them. The
bundled set is:

#include "build/colors.typ"

Hex forms may include or omit `#` and contain 3, 4, 6, or 8 hexadecimal
digits; four- and eight-digit forms include alpha. These names and hex forms
are portable to Typst and HTML. Safe Typst constructors `rgb(...)`,
`luma(...)`, `oklab(...)`, `oklch(...)`, `hsl(...)`, and `hsv(...)` are
also accepted, but HTML cannot translate them. Restrict a directive using one
of those constructors with `output=("typst",)`. ASCII ignores color styling.

== Rotated headers for compact columns

Long labels can make otherwise small numeric columns unnecessarily wide.
Select only those header cells with `i="header"`, rotate them, and leave the
first descriptive column horizontal. `alignv="b"` pins the rotated labels to
the bottom of the header row, next to the values they describe (and keeps the
first header on the same baseline); `align="l"` sets the rotated labels'
horizontal anchor. Explicit narrow widths then keep the numeric columns compact.

#tag("SOURCE")
#source("examples/03_rotated_headers.py")

#tag("RESULT")
#v(0.12em)
#include "build/03_rotated_headers.typ"

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

== Target notes to cells

A plain string in `notes` is an unmarked footer note. Use a dictionary when a
note should point back to one or more cells. Its `text` value is the footer
text, while `i` selects rows and `j` selects columns. Row selectors follow the
normal conventions (`0` is the first data row and `"header"` is the column-name
row); column names are preferred over positions.

If no `marker` is supplied, targeted notes receive superscript numbers in note
order. Set `marker` explicitly for a symbol or label such as `"*"`; the same
marker appears at every selected cell and beside the footer text. For a cell
target, supply `i`; omitting `j` targets every column in those rows. When both
selectors are lists, tytable marks their cross-product, not pairwise row/column
coordinates.

#tag("SOURCE")
#source("examples/04_targeted_notes.py")

#tag("RESULT")
#v(0.12em)
#include "build/04_targeted_notes.typ"

== List selectors

`i` and `j` accept a list of strings as well as integers, so you can name
several rows or columns in one call without repeating yourself. A list-of-strings
`j` selector like `j=["Revenue", "Cost", "Growth %"]` is self-documenting
and resilient to column reordering — no need to track integer positions.

The same works for `i`: `i=["header", "data"]` styles the column-name row
and every data row in a single directive.

#tag("SOURCE")
#source("examples/13_list_selectors.py")

#tag("RESULT")
#v(0.12em)
#include "build/13_list_selectors.typ"

== Data-driven row selectors

Instead of hard-coding row numbers, select rows by value. `i` accepts four
dynamic forms evaluated against the original DataFrame at render time:

- A #emph[Polars expression]: `i=(pl.col("Growth %") > 0) & (pl.col("Profit") > 0)`
- A Python boolean mask: `i=[False, True, False, True]`
- A boolean `pl.Series`: `i=pl.Series("review", [False, True, False, True])`
- A Python callable: `i=lambda row: row["Profit"] < 0`

Boolean lists, tuples, and Series must have exactly one value per source row;
mixed boolean/index lists are rejected. All four forms work with `.style()`,
`.fmt()`, `.plot()`, and `.images()`.
The expression or callable runs against the #emph[original] `DataFrame` (before
row-group insertion), so the column names you use are always the original ones.
Polars expressions may combine any number of columns: the example marks a row
green and bold only when growth is positive *and* profit is above zero. It also
uses an explicit review mask and a callable that targets only the `Profit` cell
in loss-making rows. South deliberately combines positive growth (`3.1`) with a
loss (`-44`), demonstrating why both sides of the expression matter.

#tag("SOURCE")
#source("examples/14_data_driven.py")

#tag("RESULT")
#v(0.12em)
#include "build/14_data_driven.typ"

== Cell-level conditional styling and formatting

The selectors answer different questions:

- `i` asks #emph[which rows?] and resolves to one boolean value per source row.
- `j` asks #emph[which columns?] and resolves names, positions, lists, or regex patterns.
- `where` asks #emph[which individual body cells?] and preserves one boolean
  output column per selected source column.

Without `where`, `i` and `j` are independent. tytable applies the directive to
every intersection of the selected rows and columns — their cross-product. For
this data:

#table(
  columns: 3,
  inset: 5pt,
  table.header([Product], [Price], [Stock]),
  [A], [150], [20],
  [B], [80], [200],
)

the following row mask selects both rows because each contains at least one
numeric value over 100:

```python
numeric = ["Price", "Stock"]

table.style(
    i=pl.any_horizontal(pl.col(numeric) > 100),
    j=numeric,
    bold=True,
)
```

`pl.any_horizontal(...)` is necessary here because `i` needs a single boolean
per row. Once both rows are selected, `j` selects both numeric columns, so all
four numeric cells become bold — including `20` and `80`. It means “style these
columns in rows where #emph[anything] matched,” not “style each value that
matched.”

Passing `i=pl.col(numeric) > 100` directly does not fix this: that expression
has two output columns rather than one row mask. Multi-output `i` expressions
are not supported; the current resolver takes only their first output column.
Use `pl.any_horizontal` / `pl.all_horizontal` for intentional row selection, or
use `where` for cell selection.

=== A mask for each numeric cell

`where` evaluates its Polars expression once against the original DataFrame.
`cs.numeric() > 100` returns boolean columns named `Price` and `Stock`, and each
true value maps back to that exact source cell. Thus `150` and `200` are styled,
while `20` and `80` are not:

#tag("SOURCE")
#source("examples/18_cell_where.py")

#tag("RESULT")
#v(0.12em)
#include "build/18_cell_where.typ"

When `where` is present, the final target is:

```text
(rows selected by i × columns selected by j) ∩ true cells selected by where
```

Omit `i` and `j` when the `where` expression already identifies everything you
need. Add either selector when it provides a useful additional restriction.

=== Restrict the mask with a boolean row column

The next example has an `Active` boolean column. `i=pl.col("Active")` removes
inactive rows, `j` limits the candidate display columns to `Price` and `Stock`,
and `where` tests each remaining cell. The inactive row B is not highlighted
even though both of its numeric values exceed 100; in active row C, only Stock
matches.

#tag("SOURCE")
#source("examples/19_cell_where_active.py")

#tag("RESULT")
#v(0.12em)
#include "build/19_cell_where_active.typ"

=== Formatting selected cells

`.fmt()` accepts the same cell mask. Every transform recorded in that one
directive — `digits`, `fn`, `replace`, `linebreak`, `math`, and `escape` — runs
only on matching cells:

```python
table = tt(df).fmt(
    where=cs.numeric() > 100,
    digits=0,
)
```

Conditions always see the original typed values, not strings produced by an
earlier formatting directive. `where` expressions also use original source
column names after `.set_name()` changes displayed headers; `j` uses those same
stable source names. False and null mask values select nothing. A mask
must have one boolean value per source row, and each output column name must
match a source column.

Because `where` maps source data cells, it never selects column headers, group
labels, captions, or notes. Continue to use `i="header"`, `i="groupi"`,
`i="groupj"`, `i="caption"`, or `i="notes"` for those synthetic targets.

= Grouping

Grouping adds visual hierarchy by placing spanning labels above related columns
or separator labels between related data rows.

== Column groups

Column groups add #emph[spanning header rows] above the regular column names, so
you can label clusters of related columns. The simplest way is to pass an
explicit delimiter: `.group(delimiter="_")` splits every column name on that
string and turns the shared prefix into a group. In the example below the dataframe has
four columns named `Q1_revenue`, `Q1_cost`, `Q2_revenue`, and `Q2_cost`; the
underscore split yields two groups — `Q1` spanning the first two columns and
`Q2` spanning the last two. For full control you can instead pass a dict mapping
each label to its column positions, e.g.
`.group(j={"Group A": [0, 1], "Group B": [2, 3]})`. These spanning header
rows are then addressable through the special selector `i="groupj"`, for
example to style every column-group label in one call.

Each explicit group must select at least one column. Its list must be a
left-to-right contiguous span with no duplicate columns, and spans within the
same dictionary may not overlap; different groups may leave ungrouped columns
between their spans. Column names and positions may be mixed. An empty `j={}`
is a no-op, while a `None` label is rejected (other labels are converted to
text).

The delimiter is a literal, non-empty string which must occur in every display
column name and split every name into the same number of parts. Adjacent equal
parts form spans; an empty part produces a blank label. The first part is the
outermost header row and the final part is the innermost. Each later
`.group(j=...)` or `.group(delimiter=...)` call adds its header row(s) outside
the existing ones, so calls stack from newest/outermost to oldest/innermost.

== Row groups

Row groups insert a #emph[labelled separator row] before a given data row,
visually breaking the table into sections. Pass `i` as a `{label: row}` dict
where `row` is the 0-based data row the divider should precede. The example
calls `.group(i={"Division B": 1})` to place a "Division B" divider in front of
the second data row. That separator row is then addressable through the special
selector `i="groupi"` — used here to render its label bold on a light grey
background.

A row-group dictionary position may range from `0` (before the first source
row) through the source row count (after the last source row); two labels in
one dictionary cannot use the same position. A run-length list must contain
exactly one non-`None` value per source row. It inserts a label before the
first row and whenever the value changes, so repeated non-adjacent values form
separate runs. The empty list is valid only for an empty table and creates no
groups. An empty dictionary is also a no-op. Group labels may otherwise be any
value and are converted to text.

#tag("SOURCE")
#source("examples/04_group.py")

#tag("RESULT")
#v(0.12em)
#include "build/04_group.typ"

= Themes

Themes provide one replaceable base appearance. Resizing and pagination are
independent layout operations.

== Styling and composition

Restrained top, header, and bottom rules give every new table the `default`
booktab treatment. Select alternating source-data rows with `.theme_striped()`,
cell borders with `.theme_grid()`, or no base styling with `.theme_plain()`.
Calling a theme method replaces the previous base appearance. Explicit
`.style()` calls always take precedence, whether they appear before or after
the theme call.

Selecting the plain theme does not clear styling, formatting, media, groups,
or other recorded intent:

```python
table = tt(df).fmt(j="Score", digits=2).theme_plain().style(i="header", bold=True)
```

For reusable project-specific looks, write an ordinary function that selects a
base and adds explicit styles. There is no separate theme registry or plugin
mechanism.

The gallery compares the four base appearances:

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

#tag("GALLERY — plain")
#v(0.12em)
#include "build/05_theme_plain.typ"

== Resize

The `.resize()` operation scales a table to fit a target size, expressed as a fraction
of the available page area. It wraps the rendered fragment in a Typst
`#layout(size => …)` block that measures the table and rescales it by a uniform
factor. This is useful when a wide table would otherwise overflow the text
column.

Three knobs control `.resize()`:

- `width` — target width as a fraction of the page content width (`1` = full
  width). Used unless `height` is given.
- `height` — target height as a fraction of the page content height. When set,
  height drives the scaling and width follows proportionally.
- `direction` — `"down"` only shrinks oversized tables, `"up"` only expands
  undersized ones, `"both"` (default) always scales to the target.

```python
from tytable import tt

# Shrink only if wider than 95% of the page; leave smaller tables alone.
tt(df).resize(width=0.95, direction="down")

# Always scale to the full page width.
tt(df).resize()
```

#tag("SOURCE")
#source("examples/12_resize.py")

#tag("RESULT")
#v(0.12em)
#include "build/12_resize.typ"

== Multipage tables

Typst figures normally keep their contents on one page. For a long table,
`.multipage()` makes tytable figures breakable while preserving their
caption, numbering, label, and reference semantics. The complete header block,
including column-group rows, repeats at the top of each page by default:

```python
tt(df, caption="Long results", label="long-results").multipage()
```

Disable header repetition when the surrounding document supplies its own page
context:

```python
tt(df).multipage(repeat_headers=False)
```

The generated Typst show rule is scoped to figures whose kind is `"tytable"`,
so images and other figures later in the document retain their own page-break
behaviour.

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

= Images & sparklines

Use `.images()` to embed existing files without Matplotlib or the optional
`images` extra. This standalone example copies three committed SVG country flags
into the default `build/07_static_images_assets/` directory, making the generated
fragment and its sibling assets portable together:

#tag("SOURCE — STATIC FILES ONLY")
#source("examples/07_static_images.py")

#tag("RESULT")
#v(0.12em)
#include "build/07_static_images.typ"

Use `.plot()` when graphics must be generated from cell values. The next
example combines those same static flags with a plotting function
`fun(values) -> matplotlib.figure.Figure` for the sparkline column. Tytable
handles generated PNG saving and path management; this plotting half requires
the `images` extra.

#tag("SOURCE — STATIC FILES + GENERATED PLOTS")
#source("examples/07_images.py")

#tag("RESULT")
#v(0.12em)
#include "build/07_images.typ"

= Putting it together

A feature-rich table built without any image dependencies — combining explicit
column groups, a row-group separator, numeric formatting, a full-width layout,
and targeted styling. A list selector formats all numeric columns in one call;
their right alignment comes automatically from their Polars dtypes.

#tag("SOURCE")
#source("examples/08_full_report.py")

#tag("RESULT")
#v(0.12em)
#include "build/08_full_report.typ"

= Advanced Python: reusable table components

The `tt()` factory is the shortest way to create a table, while `TyTable` is
the public class it returns. Import the class when a larger program needs type
annotations, reusable theme functions, dependency injection, or a report
component with a stable `build() -> TyTable` contract:

```python
from tytable import TyTable, tt

def add_brand_style(table: TyTable) -> TyTable:
    return table.style(i="header", bold=True, background="#17324d", color="white")

table: TyTable = add_brand_style(tt(df))
```

Using `tt(df)` is still preferred to spelling `TyTable(df)` directly: the
factory is the stable construction entry point, and the annotation exposes the
useful class contract without coupling application code to implementation
details.

== A report component, end to end

The following script separates four concerns that tend to become tangled in a
larger report: data preparation in Polars, design tokens, table construction,
and filesystem output. The `build()` method returns a fully configured
`TyTable`, so callers can preview it in a notebook, render it to a string, add a
one-off style, or save it themselves.

#tag("SOURCE")
#source("examples/16_advanced_pipeline.py")

#tag("RESULT")
#v(0.12em)
#include "build/16_advanced_pipeline.typ"

== Design rules for larger programs

- *Accept and return `TyTable` in reusable styling functions.* This is the
  simplest custom-theme interface and keeps those functions easy to test.
- *Keep `build()` separate from `save()`.* Building describes the table;
  saving decides where report artifacts belong. This also makes HTML previews
  and tests (`table.render("html")`) straightforward.
- *Build fresh variants when they should diverge.* Chaining methods mutate the
  table and return `self`. If a print version and a web version need different
  directives, call the component's `build()` method twice rather than trying
  to copy internal state.
- *Let Polars own data preparation.* Derived columns, sorting, aggregation,
  joins, and input validation belong before `tt(...)`; tytable should describe
  presentation intent.
- *Test rendered contracts at the right level.* Assert the prepared DataFrame
  separately, then use a small snapshot of `render("typst")` or
  `render("html")` for the table layer.

== Developing and debugging a table

Keep the function that builds a table separate from the code that fetches data,
assembles the full report, and writes production artifacts. A small preview
script can then call that function with representative data, without running
the rest of the application:

```python
# scripts/preview_sales_table.py
import polars as pl

from reports.sales_table import build_sales_table

sample = pl.DataFrame({
    "Region": ["North", "South"],
    "Revenue": [12500.0, 9875.5],
})
table = build_sales_table(sample)

print(table)
table.save("build/sales-preview.html")
table.save("build/sales-preview.typ")
```

`print(table)` works because every `TyTable` has an ASCII representation. It is
the fastest way to check the visible rows and columns, formatted values, names,
row groups, notes, and alignment from a terminal. Open `build/sales-preview.html`
in a browser when visual styling matters; HTML output does not require Jupyter.
See #link(<alternative-backends>)[Alternative backends] for the capabilities and
limitations of both previews.

For the authoritative Typst result, make a tiny wrapper document next to the
generated fragment:

```typst
// build/preview.typ
#set page(paper: "a4", margin: 2.5cm)
#set text(size: 10pt)
#include "sales-preview.typ"
```

Then leave Typst watching that wrapper in one terminal:

```sh
typst watch build/preview.typ build/preview.pdf
```

After changing the Python builder, run the preview script again. Typst notices
the regenerated fragment and recompiles the PDF. This gives a short feedback
loop while still testing the real paged backend and its surrounding page width,
fonts, and document settings.

== Data from a web source

Polars can read a stable CSV endpoint directly, and the resulting DataFrame is
no different to tytable. For reproducible reports, download or cache the input
and record its retrieval date (or a content hash) instead of making every docs
or CI build depend on the network:

```python
from pathlib import Path
import polars as pl
from tytable import tt

cache = Path("data/indicator.csv")
if not cache.exists():
    frame = pl.read_csv(STABLE_CSV_URL)
    frame.write_csv(cache)

df = pl.read_csv(cache)
tt(df, notes=["Source: provider name; retrieved 2026-07-15"]).save("build/indicator.typ")
```

In production, pin a versioned URL when the provider offers one and validate
the expected columns before building the table. This keeps a harmless upstream
schema change from silently reshaping a report.

= Alternative backends <alternative-backends>

Typst is the primary output format, but a `TyTable` can render the same recorded
intent as HTML or fixed-width terminal text. These backends are useful for
development, tests, and applications that do not need a paged document. They
are independent renderers, not conversions of the generated Typst, so use a
compiled Typst preview for final layout decisions.

== HTML

`table.render("html")` returns an HTML table fragment as a string. Jupyter calls
the same renderer automatically when a `TyTable` is the last value in a cell,
but the backend does not depend on Jupyter. In a regular script, save a browser
preview directly:

```python
table.save("build/preview.html")
```

The HTML backend represents captions, notes, row and column groups, images,
spans, alignment, and most visual cell styling. It is also convenient for web
applications and snapshot tests that need inspectable markup:

```python
html = table.render("html")
assert "Total" in html
```

HTML layout follows browser and CSS rules. Page-oriented Typst behavior such as
multipage tables, repeated page headers, and exact Typst sizing is therefore
not reproduced, and browser output should not be treated as a pixel-accurate
preview of the final PDF.

== ASCII terminal output

`print(table)`, `repr(table)`, and `table.render("ascii")` produce a fixed-width
plain-text table. An interactive Python prompt also shows this representation
when the table is the value of an expression:

```python
table = build_sales_table(sample)
print(table)

text = table.render("ascii")
assert "Revenue" in text
```

Formatting, renamed columns, row groups, and horizontal alignment are
preserved. Captions and notes are emitted as plain text, with targeted note
markers written as `[1]`, `[*]`, and so on. Cells are limited to 60 terminal
columns and truncated with an ellipsis; wide and combining Unicode characters
are measured by their terminal display width.

ASCII output intentionally omits properties that plain text cannot represent
reliably, including colors, backgrounds, font styles, rotation, and line
styling. Column-group headers and general row or column spans are not currently
represented. Use HTML for a quick visual check and compiled Typst when exact
layout matters. `.save()` infers only HTML or Typst from the destination suffix;
write the string returned by `.render("ascii")` yourself when a text artifact is
needed.

== Backend styling support

The renderers share recorded style intent, but only apply properties their
output medium can represent. In the matrix below, “yes” means the property is
rendered, “plain” means the content is retained without that styling, and “—”
means it has no meaningful representation.

#table(
  columns: (1.65fr, 1.1fr, 1.1fr, 1.1fr),
  align: (left, center, center, center),
  inset: 5pt,
  fill: (x, y) => if y > 0 and calc.odd(y) { rgb("#f4f7f8") } else { none },
  table.header(
    text(weight: "bold")[Target and property],
    text(weight: "bold")[Typst],
    text(weight: "bold")[HTML],
    text(weight: "bold")[ASCII],
  ),
  [Cell: font styles, color, size], [yes], [yes], [plain],
  [Cell: background], [yes], [yes], [—],
  [Cell: horizontal alignment], [yes], [yes], [yes],
  [Cell: vertical alignment], [yes], [yes], [—],
  [Cell: indent and rotation], [yes], [yes], [—],
  [Cell: row/column spans], [yes], [yes], [—],
  [Cell: border side/color/width], [yes], [yes], [—],
  [Cell: border trim], [yes], [—], [—],
  [Caption: font styles, color, size], [yes #super[1]], [yes], [plain],
  [Caption: background, align, indent], [—], [yes], [—],
  [Notes: font styles, color, size], [yes #super[1]], [yes], [plain],
  [Notes: background, align, indent], [yes], [yes], [—],
)

#text(size: 8.5pt)[
  #super[1] Typst caption and note text supports bold, italic, underline,
  strikeout, small caps, color, and size; HTML additionally supports monospace.
  Typst notes, unlike captions, also support background and horizontal/vertical
  alignment. Cell font styles include bold, italic, underline, strikeout,
  monospace, and small caps in both visual backends.
]

Caption and note styling is validated when that backend renders. If a directive
contains a property the selected Typst or HTML backend cannot apply, rendering
raises a targeted `ValueError`; use `output=("typst",)` or `output=("html",)`
for intentionally backend-specific styling. ASCII always emits captions and
notes as plain text and ignores their style properties. Typst-only color
constructors likewise require `output=("typst",)`; portable named and hex
colors work in both visual backends.

= Table showcase

A polished table usually needs less decoration than expected: one strong
header colour, a quiet secondary band for column groups, restrained striping,
right-aligned numbers, and a single highlight that communicates the decision.
The dtype-aware defaults supply that numeric alignment; the example only records
styles that differ from those defaults. This model scorecard combines those
choices with a targeted footnote and a Typst label for cross-referencing.

#tag("SOURCE")
#source("examples/17_showcase.py")

#tag("RESULT — publication-ready scorecard")
#v(0.12em)
#include "build/17_showcase.typ"

For other visual idioms, compare the sparse financial table in *Putting it
together*, the built-in variants in *Themes*, and the trend column in *Images &
sparklines*. Together they cover a publication table, a dense report table,
and a compact dashboard table without requiring a separate rendering system.

= Task-oriented API reference

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
  [Choose a base theme], [`.theme_striped()` / `.theme_grid()`], [chainable],
  [Adjust table layout], [`.rotate()` / `.resize()` / `.multipage()`], [chainable],
  [Add plots/images], [`.plot(...)` / `.images(...)`], [chainable],
  [Post-process output], [`.finalize(...)`], [chainable],
  [Get a string], [`.render(...)`], [`str` (terminal)],
  [Write a file], [`.save(...)`], [`None` (terminal)],
)

== Authoritative selector reference

`.style()`, `.fmt()`, `.plot()`, and `.images()` share `i` and `j`;
`.style()` and `.fmt()` additionally accept the cell-level `where` selector.
`.set_name()` shares `j`. Omitting `i` selects every genuine source-data row
for `.style()`, `.fmt()`, `.plot()`, and `.images()`.
With `j=None`, every column is selected (`.plot()` and `.images()` require an
explicit `j`; `.set_name()` instead enters full-list replacement mode).

#table(
  columns: (0.8fr, 1.45fr, 2.75fr),
  align: (left, left, left),
  inset: 6pt,
  fill: (x, y) => if y > 0 and calc.odd(y) { rgb("#f4f7f8") } else { none },
  table.header(text(weight: "bold")[Selector], text(weight: "bold")[Example], text(weight: "bold")[Meaning]),
  [`i`], [`0`, `2`, `[0, 2]`], [0-based source DataFrame row(s)],
  [`i`], [`"header"`, `"data"`], [column names or genuine source rows],
  [`i`], [`"all"`], [the complete displayed grid],
  [`i`], [`"groupi"`], [row-group separator rows],
  [`i`], [`"groupj"`], [column-group header rows],
  [`i`], [`pl.col("Score") > 80`], [Polars expression evaluated on source data],
  [`i`], [`pl.Series(...)`], [boolean mask with one value per source row],
  [`i`], [`lambda row: ...`], [predicate receiving a row dictionary],
  [`j`], [`"Score"`, `0`], [column name (preferred) or position],
  [`j`], [`["Revenue", "Cost"]`], [several columns in one directive],
  [`where`], [`cs.numeric() > 100`], [true body cells in `.style()` / `.fmt()`],
)

Non-negative integer `i` values range from zero through the source DataFrame
height minus one. Row-group separators never change what an integer selects.
`"header"` is empty when column names are hidden, and `"groupj"` is empty when
no column-group rows exist. Lists/tuples may mix integer
and string row selectors. `.style()` also accepts `i="caption"` and
`i="notes"`; these non-grid targets allow only their documented text-oriented
properties.

Data-driven `i` forms have a different coordinate system: a Polars expression,
boolean list/tuple, boolean `pl.Series`, or `callable(row_dict) -> bool` is
evaluated against the original DataFrame. Masks must be Boolean and have
exactly one entry per source row; a boolean mask cannot mix booleans with
integer selectors. Matching source rows are mapped around inserted row-group
separators. Thus use an integer for a stable source-row position, or a predicate/mask
when the target depends on source data values. `where` is also evaluated against the
original DataFrame; it must return Boolean columns with original source-column
names and the source row count. Its true cells are intersected with `i` and
`j`, and it cannot target synthetic headers, group rows, captions, or notes.

Integer `j` values range from zero through the column count minus one. Exact
string names are case-sensitive and always refer to original DataFrame column
names. Names assigned by `.set_name()` or `colnames_override` are display-only
and never match a selector unless the same string is independently an original
column name. This makes duplicate and empty display labels legal and
unambiguous. Directives recorded before and after a rename therefore select the
same columns. A list preserves its requested order and may repeat an exact
selector.

If friendly names should become the actual selector names, rename the Polars
DataFrame before constructing the table. The renamed schema then supplies both
the source identities and the initial display labels:

```python
df = df.rename({"annual_revenue_usd": "Revenue"})
table = tt(df).fmt(j="Revenue", digits=0)
```

With `regex=True`, every string element of `j` is a Python `re.search` pattern
over original DataFrame column names, not display labels or a full match. Each
pattern is limited to 500 characters and must match at least one column;
invalid patterns and no-match patterns raise `ValueError`.
Matches from a regex list are de-duplicated in first-match order. Integer
elements keep their normal meaning. Regex applies only to `j`, not `i` or
`where`.

== Creating a table

#api("Create", api_signatures.at("tt"))

`data` is a Polars `DataFrame` and is cloned on construction. The constructor
options fall into these groups:

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
)

`width` accepts a fraction, a Typst length string, or one entry per column
(fractions, strings such as `"3cm"` / `"1fr"`, and `None` may be mixed).
`gutter` accepts points as a number, a unit string, or `None`. Numeric formatting
is configured separately with `.fmt()`. A note is a string or a `NoteDict`,
exported from `tytable`. Its optional keys are `text` (footer text), `marker` (an
explicit string or `None`), `i` (row selector), and `j` (column selector):

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

== Formatting and structure

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
unchanged, and all `j` selectors continue to use its original column names.

#api("Use default appearance", api_signatures.at("theme_default"))

#api("Add stripes", api_signatures.at("theme_striped"))

#api("Add a grid", api_signatures.at("theme_grid"))

#api("Use plain appearance", api_signatures.at("theme_plain"))

This changes only the base appearance; all other recorded intent survives.

#api("Rotate", api_signatures.at("rotate"))

Rotates the whole table. Rotate selected cell content with `.style(rotate=...)`.

#api("Resize", api_signatures.at("resize"))

Scales Typst output by width or height. `direction` is `"down"`, `"up"`, or
`"both"`.

#api("Span pages", api_signatures.at("multipage"))

Makes the Typst figure breakable. Header and column-group rows repeat on each
page unless `repeat_headers=False`.

== Plots and images

Only generated plots require the optional `images` extra. `.images()` handles
existing files using only the Python standard library. Media is materialized when
the table renders or saves, not when the directive is recorded.

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
and PNG generation run during `.render()` / `.save()`. Direct Typst and HTML
renders embed the generated image bytes in the returned fragment; ASCII uses a
text placeholder. `.save()` instead writes external PNG assets.

#api("Embed files", api_signatures.at("images"))

`j` and `paths` are required. Paths are assigned row-major across selected
cells. The terminal operation's `static_images` policy determines what happens to
them:

- `"copy"` reads local files relative to the Python process's current working
  directory, gives each unique file a content-hashed name, and copies it under
  `assets`. This is the `.save()` default.
- `"reference"` emits each path or URL as authored, apart from markup escaping,
  without checking it. This is the `.render()` default and suits externally
  managed report assets and remote HTML images.
- `"embed"` reads local PNG, JPEG, GIF, or SVG files and includes their bytes in
  the Typst or HTML fragment. It creates no static-image asset, but can make the
  fragment substantially larger.

Copy and embed reject URLs, missing files, and unreadable inputs with the directive,
selected cell, and path in the error. Neither mode needs Matplotlib or the optional
`images` extra. ASCII output uses a text placeholder without reading the input.

== Rendering and output

#api("Post-process", api_signatures.at("finalize"))

Registers `fn(rendered: str, output: str) -> str`. Callbacks run in registration
order after any renderer and are useful for narrowly scoped integration markup.

#api("Render string", api_signatures.at("render"))

`output` is `"typst"`, `"html"`, or `"ascii"`. Rendering resolves all recorded
intent and runs finalizers. The same table can be rendered more than once. See
#link(<alternative-backends>)[Alternative backends] for HTML and ASCII usage,
including terminal previews with `print(table)`. A direct render of a table with
`.plot()` is self-contained: Typst embeds image bytes and HTML uses data URIs.
Rendering leaves no persistent files or directories, and repeated calls do not
retain a destination from an earlier `.save()`. Embedded plots can make these
strings large; use `.save()` when external plot files are preferable. Rendering
uses `static_images="reference"` by default. Pass `"embed"` for a self-contained
Typst or HTML string. `"copy"` raises `ValueError` because rendering has no output
location into which files could be copied.

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

Creates parent directories and infers HTML from `.html` / `.htm`; other suffixes
produce Typst. `assets` controls all externalized media: generated `.plot()` PNGs
and `.images()` inputs copied by the default `static_images="copy"` policy. A
relative value is resolved from the output file's directory and is also emitted in
the fragment; the default is a table-specific sibling `<path.stem>_assets/`
directory. Use `static_images="reference"` to retain authored paths without checks,
or `"embed"` to include supported static files in the fragment while generated
plots remain external. Each save has an independent destination and does not mutate
the table or affect a later `.render()` or `.save()` call. Generated plot names and
copied static names contain content hashes to avoid collisions; repeated static
content is copied once per save.
`save()` can additionally raise `OSError` while creating the destination directory
or writing the table or an asset. Static copy/embed can raise contextual `OSError`
for unreadable files and `ValueError` for URLs or unsupported embedded formats.
Other render-time contracts are the same as for `.render()` above.

= Saving and using a table in Typst

There are two ways to get Typst output, depending on what you want to do next:

- `table.render("typst")` returns the generated Typst source as a Python string.
  This is useful for inspecting it, changing it in Python, combining several
  fragments, or passing it to another tool. Generated `.plot()` images are packed
  into that string, so there is no separate plot folder to keep track of. The
  trade-off is that a table with several plots can produce a large string.
- `table.save("catalog.typ")` writes the Typst source to a file. This is the easy
  choice for a report. Generated plots are kept as ordinary PNG files next to it,
  which keeps the `.typ` file small.

For example, saving a table containing generated plots creates a pair like this:

```text
catalog.typ
catalog_assets/
  plot_....png
```

Keep the `.typ` file and its `_assets` folder together when moving or sharing the
table. Calling `.save()` does not compile a PDF; it prepares the table fragment and
its plot files for Typst.

This is separate from Jupyter's automatic preview. When `table` is the last value
in a notebook cell, Jupyter asks tytable for HTML and displays that result. You only
need `render("typst")` when your Python code specifically needs the Typst source as
a string.

`.save()` writes a Typst content fragment, so place it in the document with
`#include` (not `#import`, which is for importing named definitions):

```typst
// report.typ
#set page(paper: "a4", margin: 2.5cm)
#set text(size: 10pt)

= Product catalog

The current catalog is shown in @product-catalog.

#include "build/tables/catalog.typ"
```

Build the fragment first, then compile the parent document:

```sh
uv run python make_tables.py
typst compile report.typ report.pdf
```

The include path is relative to the `.typ` file containing the `#include`.
Image paths inside a generated fragment resolve from that fragment. Typst also
requires resolved files to be inside the _Typst project root_ (the directory tree
available to `typst compile`; pass `--root` when the intended root differs from
Typst's default). By default, `.save()` copies local `.images()` files and writes
generated `.plot()` files into the same asset destination. Make that destination
explicit in Python when needed:

```python
.save("build/tables/products.typ", assets="../assets/products")
```

Generated PNGs and copied static images then land in `build/assets/products/`, and
the `.typ` references `../assets/products/...`, which resolves correctly from
`build/tables/` when compiled as part of the parent. Without an explicit `assets=`,
media lands in a `<path.stem>_assets/` sibling. Keeping that sibling with the saved
fragment makes the pair relocatable and normally keeps images inside the same Typst
project tree. For HTML there is no Typst project-root restriction.

There are two deliberately different bases for relative static paths. The default
`static_images="copy"` and the `"embed"` policy open inputs relative to the Python
process's current working directory. `static_images="reference"` does not resolve
the authored value at all; after saving, a relative reference is interpreted from
the `.typ` or `.html` fragment (or its served URL). Use reference mode for remote
HTML resources or assets already managed by a surrounding report project.

= Troubleshooting

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

When an error remains unclear, first render the smallest relevant backend
directly (`table.render("typst")`, `"html"`, or `"ascii"`). This separates
tytable's generated fragment from include paths, the browser/server base URL,
and the surrounding Typst document.

= Coming from R tinytable

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
