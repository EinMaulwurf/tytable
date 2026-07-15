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

#import "build/meta.typ": commit, build_date
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
images extra when using plots, sparklines, or existing image files:

```
uv add "tytable[images]"
```

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
Typst fragment shown above.

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
6. use the API reference when you need an exact option.

= Core concepts

Four conventions make tytable chains predictable before you begin combining
formatting, styling, and grouping directives.

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

`.fmt()` and `.style()` use the intersection of `i` and `j`, so combining them
targets individual cells—for example, `.fmt(i=1, j="Score", digits=1)` formats
only the `Score` cell in the second data row, and `.style(i=1, j="Score",
bold=True)` styles only that cell.

== Everything returns `self`

`.style()`, `.fmt()`, `.group()`, `.set_name()`, and `.theme()` all return the
table, so you chain them. `.render()` and `.save()` are terminal.

== Evaluation is lazy

Styling, formatting, grouping, and plotting are recorded as _intent_ and
replayed in a fixed order at render time. Row indices always refer to the final,
visible table.

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

== In Polars

The most capable option: do everything #emph[before] passing the dataframe to
`tt()`. Polars expressions can round, cast numbers to strings, swap the decimal
delimiter, prepend a currency symbol, add thousands separators, and fill nulls —
anything Polars can express, the table will render. Here revenue is rounded to
two decimals, formatted as USD with thousands separators, and nulls filled with
an em dash, all before `tt()` ever sees the data:

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

== Styling cells

Apply per-cell styling through selectors `i` (rows) and `j` (columns).
Supported properties: `bold`, `italic`, `underline`, `strikeout`, `monospace`,
`smallcaps`, `color`, `background`, `fontsize`, `align` (`l`/`c`/`r`), `alignv`
(`t`/`m`/`b`), `indent`, `colspan`, `rowspan`, and per-side borders (`line="tblr"`
in any combination, with `line_color` / `line_width`).

Any number of these properties can be combined in a single `.style()` call when
they share the same `i`/`j` selector — e.g.
`style(j="Score", align="r", background="#eee", bold=True)` is one directive
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

== List selectors

`i` and `j` accept a list of strings as well as integers, so you can name
several rows or columns in one call without repeating yourself. A list-of-strings
`j` selector like `j=["Revenue", "Cost", "Growth %"]` is self-documenting
and resilient to column reordering — no need to track integer positions.

The same works for `i`: `i=["header", "body"]` styles the column-name row
and every data row in a single directive.

#tag("SOURCE")
#source("examples/13_list_selectors.py")

#tag("RESULT")
#v(0.12em)
#include "build/13_list_selectors.typ"

== Data-driven row selectors

Instead of hard-coding row numbers, select rows by value. `i` accepts three
dynamic forms evaluated against the original DataFrame at render time:

- A #emph[Polars expression]: `i=(pl.col("Growth %") > 0) & (pl.col("Profit") > 0)`
- A boolean `pl.Series`: `i=pl.Series("review", [False, True, False, True])`
- A Python callable: `i=lambda row: row["Profit"] < 0`

All three work with `.style()`, `.fmt()`, `.plot()`, and `.images()`.
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

The public `THEMES` constant is a dictionary mapping each built-in name to its
theme callable. Import it with `from tytable import THEMES` to inspect available
themes (`list(THEMES)`) or retrieve a callable for reuse in a custom theme. The
registry should be treated as read-only; pass custom callables directly to
`tt(theme=...)` or `.theme(...)` instead of modifying it.

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

Use `.images()` to embed existing files and `.plot()` to generate graphics from
cell values. This example adds three committed SVG country flags, then supplies
a plotting function `fun(values) -> matplotlib.figure.Figure` for the sparkline
column. Tytable handles generated PNG saving and path management. Both methods
require the `images` extra.

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

= Table showcase

A polished table usually needs less decoration than expected: one strong
header colour, a quiet secondary band for column groups, restrained striping,
right-aligned numbers, and a single highlight that communicates the decision.
This model scorecard combines those choices with a targeted footnote and a
Typst label for cross-referencing.

#tag("SOURCE")
#source("examples/17_showcase.py")

#tag("RESULT — publication-ready scorecard")
#v(0.12em)
#include "build/17_showcase.typ"

For other visual idioms, compare the sparse financial table in *Putting it
together*, the built-in variants in *Themes*, and the trend column in *Images &
sparklines*. Together they cover a publication table, a dense report table,
and a compact dashboard table without requiring a separate rendering system.

= API reference

Start here when you know the task but not the method. Methods marked
*chainable* mutate the `TyTable` and return `self`; output methods are terminal.

#table(
  columns: (1.15fr, 1.2fr, 2.65fr),
  align: (left, left, left),
  inset: 6pt,
  stroke: (x, y) => if y == 0 { (bottom: 0.7pt + rgb("#153243")) } else { none },
  table.header(
    text(weight: "bold")[Task],
    text(weight: "bold")[Use],
    text(weight: "bold")[Result],
  ),
  [Create], [`tt(...)`], [`TyTable`],
  [Style cells], [`.style(...)`], [chainable],
  [Format values], [`.fmt(...)`], [chainable],
  [Group rows/columns], [`.group(...)`], [chainable],
  [Rename headers], [`.set_name(...)`], [chainable],
  [Apply a theme], [`.theme(...)`], [chainable],
  [Add plots/images], [`.plot(...)` / `.images(...)`], [chainable],
  [Post-process output], [`.finalize(...)`], [chainable],
  [Get a string], [`.render(...)`], [`str` (terminal)],
  [Write a file], [`.save(...)`], [`None` (terminal)],
)

== Selector cheat sheet

`.style()`, `.fmt()`, `.plot()`, and `.images()` share the same selectors;
`.set_name()` shares the column selector. Names are exact matches by default.

#table(
  columns: (0.8fr, 1.45fr, 2.75fr),
  align: (left, left, left),
  inset: 6pt,
  fill: (x, y) => if y > 0 and calc.odd(y) { rgb("#f4f7f8") } else { none },
  table.header(
    text(weight: "bold")[Selector],
    text(weight: "bold")[Example],
    text(weight: "bold")[Meaning],
  ),
  [`i`], [`0`, `2`, `[0, 2]`], [0-based data row(s)],
  [`i`], [`"header"`, `"body"`], [column names or all data rows],
  [`i`], [`"groupi"`, `"groupj"`], [row- or column-group header rows],
  [`i`], [`-1`], [topmost column-group header row],
  [`i`], [`pl.col("Score") > 80`], [Polars expression evaluated on source data],
  [`i`], [`pl.Series(...)`], [boolean mask with one value per source row],
  [`i`], [`lambda row: ...`], [predicate receiving a row dictionary],
  [`j`], [`"Score"`, `0`], [column name (preferred) or position],
  [`j`], [`["Revenue", "Cost"]`], [several columns in one directive],
)

Set `regex=True` on an individual method call to treat its string `j`
selectors as `re.search` patterns. `.style()` also accepts `i="caption"` and
`i="notes"`; those targets support text-oriented properties rather than cell
spans or borders.

== Creating a table

#api("Create", api_signatures.at("tt"))

`data` is a Polars `DataFrame` and is cloned on construction. The constructor
options fall into four groups:

#table(
  columns: (1.05fr, 1.9fr, 2.05fr),
  align: (left, left, left),
  inset: 5pt,
  table.header(
    text(weight: "bold")[Concern],
    text(weight: "bold")[Options],
    text(weight: "bold")[Notes],
  ),
  [Figure], [`figure`, `caption`, `label`, `notes`], [captions and labels require `figure=True`],
  [Layout], [`width`, `height`, `gutter`], [`width=1` fills the line; lists set each column],
  [Headers], [`colnames`, `colnames_override`], [show and rename display headers],
  [Values], [`digits`, `escape`], [global numeric precision and safe markup],
  [Behaviour], [`theme`, `finalize`], [initial theme and output callback],
  [Reserved], [`rownames`], [present for parity; not implemented],
)

`width` accepts a fraction, a Typst length string, or one entry per column
(fractions, strings such as `"3cm"` / `"1fr"`, and `None` may be mixed).
`gutter` accepts points as a number, a unit string, or `None`. A note is a
string or a dictionary with `text`, `marker`, `i`, and `j` keys.

`TyTable(...)` has the same constructor options, but application code should
normally construct with `tt(...)` and use `TyTable` for annotations.

== Formatting and structure

#api("Style", api_signatures.at("style"))

Combines any properties sharing one selector. `align` uses `l`/`c`/`r`,
`alignv` uses `t`/`m`/`b`, `rotate` is degrees, and `line` is any combination
of `t`/`b`/`l`/`r`. With several columns, `align="llr"` assigns one alignment
per column. `fontsize`, `indent`, and `line_width` are in `em`. `output` can
restrict a directive to a tuple such as `("typst",)`.

#api("Format", api_signatures.at("fmt"))

Transforms values in this order: `digits`, `replace`, `escape`, `fn`.
`num_fmt` is `"decimal"` or `"significant"`; `replace` may blank missing
values, supply a replacement string, or map old values to new ones. `fn`
receives one column as `list[str]` and must return a list of the same length.

#api("Group", api_signatures.at("group"))

For row groups, pass `{label: row}` or a list with one group value per data row.
For spanning column headers, pass `{label: [columns]}` as `j`, or pass a literal
string as `delimiter` to split every column name. `j` and `delimiter` are
mutually exclusive.

#api("Rename display headers", api_signatures.at("set_name"))

With `j`, `name` is one display name or a list matching the selected columns.
Without `j`, pass the complete list of display names. The DataFrame remains
unchanged; later `j` selectors use the new display names.

#api("Theme", api_signatures.at("theme"))

`name` is a built-in theme name, a callable `theme(table) -> TyTable`, or
`None`. Built-ins are `default`, `striped`, `grid`, `empty`, `rotate`, and
`resize`; `THEMES` exposes the registry of callables, which should be treated
as read-only.

== Plots and images

Install the `images` extra for both methods. Media is materialized when the
table renders or saves, not when the directive is recorded.

#api("Generate plots", api_signatures.at("plot"))

`j` and `fun` are required. The callable receives the typed cell value (or the
matching `data` entry) and returns a Matplotlib `Figure` or `plotnine` plot. Pixel
dimensions control PNG generation; `height` controls its displayed cell size.

#api("Embed files", api_signatures.at("images"))

`j` and `paths` are required. Paths are assigned row-major across selected
cells. Use `.save(..., assets=...)` to control where referenced files live.

== Rendering and output

#api("Post-process", api_signatures.at("finalize"))

Registers `fn(rendered: str, output: str) -> str`. Callbacks run in registration
order after any renderer and are useful for narrowly scoped integration markup.

#api("Render string", api_signatures.at("render"))

`output` is `"typst"`, `"html"`, or `"ascii"`. Rendering resolves all recorded
intent and runs finalizers. The same table can be rendered more than once.

#api("Save file", api_signatures.at("save"))

Creates parent directories and infers HTML from `.html` / `.htm`; other
suffixes produce Typst. `assets` is relative to the output file and defaults to
a sibling `tytable_assets/` directory.

= Using a generated table in Typst

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
Generated image references need a little more care: they must resolve within
the _Typst project root_ (the directory tree available to `typst compile`). Make
the assets location explicit in Python:

```python
.save("build/tables/products.typ", assets="../assets/products")
```

Images then land in `build/assets/products/` and the `.typ` references
`../assets/products/...`, which resolves correctly from `build/tables/` when
compiled as part of the parent. Without an explicit `assets=`, images land in a
`tytable_assets/` folder next to the output file.

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
  [`theme_tt(x, ...)`], [`.theme(...)` / `tt(theme=...)`],
  [`print(x, "typst")`], [`.render("typst")`],
  [`save_tt(x, "out.typ")`], [`.save("out.typ")`],
  [`x %>% format(...) %>% ...`], [`.fmt(...).style(...)` — method chain],
  [`colnames(x) <- c(...)`], [`.set_name(name=[...])`],
  [1-based rows; 0 = colnames], [*0-based* data rows; `i="header"`],
  [column by integer position], [column by *name* (preferred)],
)
