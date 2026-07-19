#import "_common.typ": source, tag

= — Learn tytable <learn-guide>

Read this part from beginning to end. It introduces the core workflow one concern at a time and finishes with complete report output.

== Introduction

#text(weight: "bold")[tytable] is a small Python library that turns Polars
DataFrames into Typst tables. It is inspired by R's
#link("https://github.com/vincentarelbundock/tinytable")[tinytable] package and
mirrors most of its styling power, including image and sparkline support plus
a Jupyter HTML preview.

=== What is Typst?

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

=== Why tytable exists

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
== Start here: your first table

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

=== Make one column easier to read

Now add one formatting decision. Column names are used directly, so this reads
as “show Price with two decimal places”:

```python
table = tt(data).fmt(j="Price", digits=2)
```

=== Add one visual cue

Styling is another chained instruction. A header treatment is a useful first
one because it does not depend on the number of data rows:

```python
table = (
    tt(data)
    .fmt(j="Price", digits=2)
    .style(i="header", bold=True, background="#17324d", color="white")
)
```

=== Put it in a report

Add figure metadata when the table becomes part of a larger document, then
save it:

#tag("SOURCE")
#source("examples/01_report_ready.py")

#tag("RESULT — ready for the report")
#v(0.12em)
#include "build/tables/catalog.typ"

The generated file can be `#include`-ed in a Typst report. Refer to the
numbered figure there with `@product-catalog`.

=== The storyline from here

This documentation is organized into three parts. *Learn tytable* grows that
first table one concern at a time. *Recipes and advanced topics* collects
independent solutions for wider tables, media, alternate backends, and reusable
components. *Reference* provides complete selectors, signatures, error
contracts, troubleshooting, and migration notes.

The recommended path is:

1. understand rows, columns, and chaining;
2. format values and rename display headers;
3. add styling, groups, themes, and layout;
4. embed plots and assemble a complete report table;
5. turn the same chain into a reusable, typed Python component;
6. use the task-oriented API reference to find the method for a job.
== Core concepts

Four conventions make tytable chains predictable before you begin combining
formatting, styling, and grouping directives.

=== Row selectors are semantic

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

=== Select columns by name

`j="Score"` is the preferred form; `j=0` selects the first column by position.
Both `i` and `j` also accept sequences of strings or integers to target several rows or columns in
one call: `j=["Q1 Rev", "Q1 Cost"]`, `i=["header", "data"]`, or `j=range(5)`
for the first five columns. Lists, tuples, and ranges are supported; arbitrary
iterables such as generators and sets are not. `i` additionally
accepts Polars expressions, boolean series, and callables for data-driven
selection (see the *Styling* section).

`.fmt()` and `.style()` use the intersection of `i` and `j`, so combining them
targets individual cells—for example, `.fmt(i=1, j="Score", digits=1)` formats
only the `Score` cell in the second data row, and `.style(i=1, j="Score",
bold=True)` styles only that cell.

=== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, `.set_name()`, the `.theme_*()` methods, and
the named layout operations all return the table, so you chain them.
`.render()` and `.save()` are terminal.

=== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Integer row selectors always refer to
stable, 0-based source DataFrame rows.
== Renaming columns

`.set_name()` renames column headers for display without touching the
underlying Polars `DataFrame` — the original frame is never modified. This is
useful when the Polars column names are machine-friendly identifiers but you
want human-readable headers in the rendered table, or when you need a header
that Polars would reject as a column name (such as an empty string `""` or a
duplicate).

Three calling modes:

- *Per-column*: `.set_name(j, name=...)` renames the column(s) selected by `j`.
  `j` follows the same selector rules as `.style()` / `.fmt()` (name, integer
  position, a list, or a regex with `regex=True`; see `.style()`). `name` is a
  single `str` (applied to every matched column) or a `list[str]` with one entry
  per match.
- *Full-list replace*: `.set_name(name=[...])` (omit `j`) replaces every column
  header at once — the list length must equal the column count.
- *Mapping*: `.set_name(name={source: display, ...})` renames any subset using
  exact original DataFrame column names as keys.

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
== Formatting

Cell values can be formatted in three complementary ways. Pick whichever suits
the column, or mix them across columns in the same table.

=== In Polars

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

=== With `.fmt()`

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

=== With `.fmt(fn=...)`

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
== Styling

Styling directives control the appearance of cells and table-adjacent text
without changing the underlying values.

By default, text columns and their headers are left-aligned, while columns with
Polars numeric dtypes and their headers are right-aligned. Alignment is inferred
from the source dtype before `.fmt()` changes the displayed text, so formatted
numbers, replacement marks, currencies, and percentages stay aligned. An explicit
`.style(align=...)` directive takes precedence. Column-group headers are centered.

=== Styling cells

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

=== Color values and backend scope

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

=== Rotated headers for compact columns

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

=== Caption and notes

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

=== Target notes to cells

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

=== Sequence selectors

`i` and `j` accept sequences of strings as well as integers, so you can name
several rows or columns in one call without repeating yourself. A list-of-strings
`j` selector like `j=["Revenue", "Cost", "Growth %"]` is self-documenting
and resilient to column reordering — no need to track integer positions.

Ranges are convenient for positional spans: `j=range(5)` selects the first
five columns, while `i=range(5)` selects the first five source rows. Tuples are
also accepted. Arbitrary iterables such as generators and sets are rejected so
deferred selectors remain deterministic across repeated renders.

The same works for `i`: `i=["header", "data"]` styles the column-name row
and every data row in a single directive.

#tag("SOURCE")
#source("examples/13_list_selectors.py")

#tag("RESULT")
#v(0.12em)
#include "build/13_list_selectors.typ"

=== Data-driven row selectors

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

=== Cell-level conditional styling and formatting

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
== Grouping

Grouping adds visual hierarchy by placing spanning labels above related columns
or separator labels between related data rows.

=== Column groups

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

=== Row groups

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
== Themes

Themes provide one replaceable base appearance. Resizing and pagination are
independent layout operations.

=== Styling and composition

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

=== Resize

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

=== Multipage tables

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
== Saving and using a table in Typst

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
== Putting it together

A feature-rich table built without any image dependencies — combining explicit
column groups, a row-group separator, numeric formatting, a full-width layout,
and targeted styling. A list selector formats all numeric columns in one call;
their right alignment comes automatically from their Polars dtypes.

#tag("SOURCE")
#source("examples/08_full_report.py")

#tag("RESULT")
#v(0.12em)
#include "build/08_full_report.typ"
