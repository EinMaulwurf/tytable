#import "_common.typ": source, tag

= — Learn tytable <learn-guide>

Read this part from beginning to end. It introduces the core workflow one
concern at a time and finishes with complete report tables.

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

A minimal parent document can live beside the `build/` directory:

#block(breakable: false)[
```typst
// report.typ
#set page(paper: "a4", margin: 2.5cm)

= Product catalog

The current catalog is shown in @product-catalog.

#include "build/tables/catalog.typ"
```
]

After the Python script has created the table fragment, compile the parent
document with `typst compile report.typ`.

=== The storyline from here

This document has three parts. Read @learn-guide[] in order to learn the normal
tytable workflow, from a first DataFrame through a table included in a Typst
report. @advanced-guides[] contains optional recipes for conditional selection,
difficult layouts, images, alternative backends, and larger Python programs.
@api-reference[] is the lookup reference for methods, selectors, and common
errors.

== Core concepts

Four conventions make tytable chains predictable before you begin combining
formatting, styling, and grouping directives.

=== Row indexing is 0-based

`i=0` is the first _data_ row (the row *after* the column-name header). Use
`i="header"` for the column-name row and `i="body"` for every table-body row.
The explicit `"body"` selector is useful when you want to leave headers
unchanged. Negative integers select column-group header rows (`-1` is the
innermost row, immediately above the column-name header; increasingly negative
values move upward). Row-group separator rows are addressed with `i="groupi"`,
genuine data rows excluding those separators with `i="~groupi"`, and
column-group rows with `i="groupj"`.

=== Select columns by name

`j="Score"` is the preferred form; `j=0` selects the first column by position.
Both `i` and `j` also accept a #emph[list] of strings or integers to target several rows or columns in
one call: `j=["Q1 Rev", "Q1 Cost"]`, `i=["header", "body"]`. `i` additionally
accepts Polars expressions, boolean series, and callables for data-driven
selection (see *Selecting rows, columns, and individual cells* in
@advanced-guides[]).

`.fmt()` and `.style()` use the intersection of `i` and `j`, so combining them
targets individual cells—for example, `.fmt(i=1, j="Score", digits=1)` formats
only the `Score` cell in the second data row, and `.style(i=1, j="Score",
bold=True)` styles only that cell.

=== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, `.set_name()`, and the `.theme_*()` methods
all return the table, so you chain them. `.theme(fn)` applies a custom theme
callable. `.render()` and `.save()` are terminal.

=== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Row indices always refer to the final,
visible table.

== Renaming columns

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

After renaming, subsequent `j` selectors use the _new_ display names; the old
polars column name no longer matches. The example starts from
`grp`, `val_1`, `val_2` and replaces them with `""`, `Revenue`, `Cost` — then
formats the renamed columns by their new names. Their alignment continues to
follow the numeric dtypes of the underlying source columns:

#tag("SOURCE")
#source("examples/15_set_name.py")

#tag("RESULT")
#v(0.12em)
#include "build/15_set_name.typ"

For one-off renames at construction time, `tt(df, colnames_override={old: new})`
does the same thing without a chained call.

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

Use `i="body"` when a style should apply to every table-body row while leaving
the header rows alone. The example below uses it to draw the left and right
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

Themes bundle reusable appearance and layout choices behind chainable methods.
This chapter covers the everyday styling themes. @advanced-guides[] collects
the layout recipes for rotated headers, resizing, and pagination.

=== Styling and composition

Restrained top, header, and bottom rules give every new table the `default`
booktab treatment. Add striping with `.theme_striped()` or cell borders with
`.theme_grid()`. Themes stack, so both can be combined with the default rules
and the layout themes described in @advanced-guides[]. Explicit `.style()` calls
retain precedence over the deferred default and striped styles.

`.theme_empty()` is the escape hatch for a blank slate. It clears all themes,
styles, formats, prepare hooks, and theme-level Typst options recorded before
it, so call it immediately after `tt(...)` and before adding anything that
should remain:

```python
table = tt(df).theme_empty().fmt(j="Score", digits=2).style(i="header", bold=True)
```

Use `.theme(custom_theme)` for a custom callable accepting the table and
returning it (or `None`). The public `THEMES` registry remains available for
discovery and advanced composition, but normal application code should prefer
the typed methods.

`THEMES` is a dictionary with the keys `"default"`, `"striped"`, `"grid"`,
`"empty"`, `"rotate"`, `"resize"`, and `"multipage"`. Every value is a
callable whose first argument is a `TyTable`; it mutates that table and returns
the same object. `default`, `striped`, `grid`, and `empty` have the shape
`fn(table)`. `rotate` adds `angle=90, i=None, j=None`; `resize` adds
`width=1, height=None, direction="both"`; and `multipage` adds the keyword-only
`repeat_headers=True`. Registry functions are useful for discovery or custom
composition, for example `THEMES["grid"](table)`, but `.theme_grid()`,
`.theme_resize(...)`, and the other typed methods are the recommended,
IDE-friendly interface.

The gallery compares the default, stacked striped and grid treatments, and the
unstyled result:

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


== Saving and using a table in Typst

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
Image paths inside a generated fragment resolve from that fragment, whether they
came from `.images()` or `.plot()`. Typst also requires resolved files to be inside
the _Typst project root_ (the directory tree available to `typst compile`; pass
`--root` when the intended root differs from Typst's default). For generated plots,
make the assets location explicit in Python:

```python
.save("build/tables/products.typ", assets="../assets/products")
```

Generated PNGs then land in `build/assets/products/` and the `.typ` references
`../assets/products/...`, which resolves correctly from `build/tables/` when
compiled as part of the parent. Without an explicit `assets=`, generated PNGs land
in a `tytable_assets/` folder next to the output file. In contrast, `.images()`
paths are never checked, copied, or rewritten by `assets=`. For HTML, relative
`src` paths likewise resolve from the saved HTML file (or its served URL), but
there is no Typst project-root restriction.


== Putting it together

The final two examples combine the ideas from @learn-guide[] into complete,
publication-ready tables.

=== A complete report table

A feature-rich table built without any image dependencies — combining explicit
column groups, a row-group separator, numeric formatting, a full-width layout,
and targeted styling. A list selector formats all numeric columns in one call;
their right alignment comes automatically from their Polars dtypes.

#tag("SOURCE")
#source("examples/08_full_report.py")

#tag("RESULT")
#v(0.12em)
#include "build/08_full_report.typ"


=== Publication-ready scorecard

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
