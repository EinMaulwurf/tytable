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

Tytable-generated `.typ` fragments require *Typst 0.11.1 or newer* to compile.
The published documentation PDF is built with Typst 0.15.0.

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

Two conventions make tytable chains predictable before you begin combining
formatting, styling, and grouping directives.

Everything returns `self`: `.style()`, `.fmt()`, `.group()`, `.set_name()`, the `.theme_*()` methods, and
the named layout operations all return the table, so you chain them.
`.render()` and `.save()` are terminal.

Evaluation is lazy: Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Integer row selectors always refer to
stable, 0-based source DataFrame rows.

== Select rows and columns <selectors>

Methods that act on part of a table use `i` to select rows and `j` to select columns. This includes `.fmt()`, `.style()`, `.plot()`, `.images()`, and targeted notes. A targeted note puts the same selectors in a `NoteDict` passed to `tt(..., notes=[...])`:

```python
from tytable import NoteDict

important: NoteDict = {"text": "Important value", "i": 0, "j": "Score"}
table = tt(df, notes=[important])
```

The small calls below only illustrate selection; #link(<formatting>)[Formatting], #link(<styling>)[Styling], and #link(<target-notes>)[Target notes to cells] introduce the operations themselves in more detail.

=== Select rows with `i`

Non-negative integers are 0-based positions in the original DataFrame, so `i=0`
always means the first source row. Inserting row groups does not change that
meaning. Negative row positions are not supported. Omit `i`, pass `None`, or use
`i="data"` to select every genuine source-data row.

Use a list, tuple, or range to select several rows:

```python
table.style(i=0, bold=True)          # first source row
table.style(i=range(3), bold=True)   # first three source rows
```

Structural rows have semantic names:

#table(
  columns: (auto, 1fr),
  inset: 5pt,
  align: (left, left),
  table.header([Selector], [Target]),
  [`"data"`], [all genuine source-data rows],
  [`"header"`], [the column-name row],
  [`"groupi"`], [inserted row-group separator rows],
  [`"groupj"`], [spanning column-group header rows],
  [`"all"`], [the complete displayed grid],
  [`"caption"`], [the caption; `.style()` only],
  [`"notes"`], [all footer notes; `.style()` only],
)

Sequences may mix positions and semantic names, such as
`i=[0, 2, "header"]`. Lists, tuples, and ranges are supported; generators and
sets are not.

Rows may also be selected from their source values:

```python
table.style(i=pl.col("Score") >= 80, bold=True)
table.style(i=[True, False, True], bold=True)
table.style(i=pl.Series([True, False, True]), bold=True)
table.style(i=lambda row: row["Score"] >= 80, bold=True)
```

Boolean masks and Series need exactly one value per source row. Expressions and callables are evaluated against the original DataFrame. All four forms work with `.style()`, `.fmt()`, `.plot()`, `.images()`, and the `i` key of a targeted `NoteDict`.

The selector vocabulary is shared, but operations accept only row kinds they
can represent. `.style()` supports every grid row as well as captions and notes;
`.fmt()` and targeted notes support data, `"header"`, and `"groupi"`; `.plot()`
and `.images()` support data and `"groupi"`. Unsupported structural selections
raise an error during rendering.

=== Select columns with `j`

Select columns by their original DataFrame names whenever possible. Integer
positions, sequences, and ranges are also supported. Omitting `j` selects every
column.

```python
table.fmt(j="Score", digits=1)
table.style(j=["Name", "Score"], bold=True)
table.style(j=range(2), bold=True)
```

With `regex=True`, strings are regular expressions matched against the original column names using Python's `re.search`. This works in a `NoteDict` as well as in method calls:

```python
table.fmt(j=r"^Q[1-4]$", regex=True, digits=1)
quarter_note = NoteDict(text="Quarterly value", j=r"^Q[1-4]$", regex=True)
```

Names assigned by `.set_name()` are display labels, not selectors. Continue to
use the original DataFrame name after renaming a header.

=== Combine rows and columns, or select individual cells

Combining `i` and `j` selects their rectangular cross-product. This call acts
on just the `Score` cell in the second source row:

```python
table.style(i=1, j="Score", bold=True)
```

Use `where` with `.style()`, `.fmt()`, or a targeted `NoteDict` when a condition should select individual data cells instead of complete rows:

```python
import polars.selectors as cs

table.style(where=pl.col("Score") >= 80, bold=True)
high_values = NoteDict(text="Value exceeds 100", where=cs.numeric() > 100)
table = tt(df, notes=[high_values])
```

A `where` expression is evaluated against the original typed DataFrame. Its
Boolean output columns are matched to source columns by name and intersected
with any `i` and `j` selection:

```text
(rows selected by i × columns selected by j) ∩ true cells selected by where
```

An `i` expression must resolve to one Boolean value per source row; use
`pl.any_horizontal` or `pl.all_horizontal` to reduce a multi-column condition.
A `where` expression instead preserves its Boolean output columns so each true
value maps to one source cell. Each output column name must match a source
column, and false or null values select nothing.

Both forms always see the original typed values and original column names,
including after `.set_name()`. `where` cannot target headers, group rows,
captions, or notes.

=== Selectors at a glance

Every panel below starts from the same four-row table, including its `Results` column group and inserted `Group B` row. The selector printed above it is the only selection that changes; green shows every cell it targets.

#let selector-card(label, result) = block(
  width: 100%,
  breakable: false,
  fill: rgb("#f7f9f8"),
  stroke: 0.5pt + rgb("#dfe6e2"),
  inset: 4pt,
  radius: 5pt,
)[
  #block(height: 2.1em)[#text(size: 8.5pt)[#raw(label, lang: "python")]]
  #v(2pt)
  #align(center)[#scale(64%, reflow: true)[#result]]
]

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 7pt,
  row-gutter: 5pt,
  selector-card("i=0", [#include "build/20_selector_i0.typ"]),
  selector-card("i=[0, 2]", [#include "build/20_selector_ilist.typ"]),
  selector-card("i=pl.col(\"Score\") > 100", [#include "build/20_selector_iexpr.typ"]),
  selector-card("j=\"Sales\"", [#include "build/20_selector_jname.typ"]),
  selector-card("i=1, j=[\"Sales\", \"Cost\"]", [#include "build/20_selector_ij.typ"]),
  selector-card("i=pl.col(\"Score\") > 100,\nj=[\"Sales\", \"Cost\"]", [#include "build/20_selector_crossproduct.typ"]),
  selector-card("where=cs.numeric() > 100", [#include "build/20_selector_where.typ"]),
  selector-card("i=\"header\"", [#include "build/20_selector_header.typ"]),
  selector-card("i=[\"groupi\", \"groupj\"]", [#include "build/20_selector_groups.typ"]),
)

The middle-right panel highlights four cells because `i` selects two rows and `j` selects two columns: the selectors form a 2 × 2 cross-product, regardless of the values in `Sales` and `Cost`. The lower-left `where` example instead tests cells individually and highlights only numeric values over 100.

== Renaming columns

`.set_name()` renames column headers for display without touching the
underlying Polars `DataFrame` — the original frame is never modified. This is
useful when the Polars column names are machine-friendly identifiers but you
want human-readable headers in the rendered table, or when you need a header
that Polars would reject as a column name (such as an empty string `""` or a
duplicate).

Three calling modes:

- *Per-column*: `.set_name(j, name=...)` renames the column(s) selected by `j`.
  `j` follows the #link(<selectors>)[column selector rules] (name, integer
  position, a list, or a regex with `regex=True`). `name` is a
  single `str` (applied to every matched column) or a `list[str]` with one entry
  per match.
- *Full-list replace*: `.set_name(name=[...])` (omit `j`) replaces every column
  header at once — the list length must equal the column count.
- *Mapping*: `.set_name(name={source: display, ...})` renames any subset using
  exact original DataFrame column names as keys.

Because #link(<selectors>)[selectors keep using source-column names], display
labels may safely be duplicate or empty. This example displays `""`, `Revenue`,
and `Cost`, then formats the last two columns using their source names `val_1`
and `val_2`. Their alignment continues to follow the source-column numeric
dtypes:

#tag("SOURCE")
#source("examples/15_set_name.py")

#tag("RESULT")
#v(0.12em)
#include "build/15_set_name.typ"

== Formatting <formatting>

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
reaching back into polars. See #link(<selectors>)[Select rows and columns] to
restrict any transform to particular rows, columns, or conditionally selected
cells.

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
== Styling <styling>

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

See #link(<selectors>)[Select rows and columns] for positional, semantic,
data-driven, and individual-cell selection.

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

=== Target notes to cells <target-notes>

A plain string in `notes` is an unmarked footer note. Use a dictionary when a note should point back to one or more cells. Its `text` value is the footer text, while `i`, `j`, `where`, and `regex` follow the #link(<selectors>)[same selector rules as `.fmt()` and `.style()`]. `NoteDict`, exported from `tytable`, is an optional typing convenience that helps type checkers and IDEs validate and suggest the available keys. The example shows both `note: NoteDict = {...}` and `note = NoteDict(...)`; they are identical at runtime and both create ordinary dictionaries.

If no `marker` is supplied, targeted notes receive superscript numbers in note order. Set `marker` explicitly for a symbol or label such as `"*"`; the same marker appears at every selected cell and beside the footer text. With `i` and `j`, omitting either axis selects its complete data region; when both selectors contain several entries, tytable uses their normal cross-product, not pairwise row/column coordinates. Use `where` for cell-by-cell selection; in the example, `cs.numeric() > 130` marks only numeric cells whose own value exceeds 130.

#tag("SOURCE")
#source("examples/04_targeted_notes.py")

#tag("RESULT")
#v(0.12em)
#include "build/04_targeted_notes.typ"

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

=== Resize <resize>

The `.resize()` operation scales a table to fit a target size, expressed as a fraction
of the available page area. It wraps the rendered fragment in a Typst
`#layout(size => …)` block that measures the table and rescales it by a uniform
factor. This is useful when a wide table would otherwise overflow the text
column.

This is different from `tt(width=...)`, which assigns available width among
columns without scaling their contents, and `tt(height=...)`, which sets row
height in `em`. See #link(<column-widths>)[Column widths] for column layout.

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

== Saving and using a table in Typst <saving-typst>

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
