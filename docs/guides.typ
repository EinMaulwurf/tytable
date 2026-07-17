#import "_common.typ": source, tag

#pagebreak()

= — Recipes and advanced topics <advanced-guides>

The chapters in this part are independent. Read the ones that match the table
or application you are building.

== Selecting rows, columns, and individual cells

The basic selectors from @learn-guide[] cover most tables. Use the following
forms when the target depends on several names, source-data values, or a
condition evaluated separately for every body cell.

=== List selectors

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

==== A mask for each numeric cell

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

==== Restrict the mask with a boolean row column

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

==== Formatting selected cells

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
column names after `.set_name()` changes displayed headers; `j` continues to
use the new display names. False and null mask values select nothing. A mask
must have one boolean value per source row, and each output column name must
match a source column.

Because `where` maps source data cells, it never selects column headers, group
labels, captions, or notes. Continue to use `i="header"`, `i="groupi"`,
`i="groupj"`, `i="caption"`, or `i="notes"` for those synthetic targets.


== Wide and long tables

When natural table dimensions do not fit the page, first control column widths,
then consider rotated headers, scaling, or pagination.

=== Column widths

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


=== Resize

The `resize` theme scales a table to fit a target size, expressed as a fraction
of the available page area. It wraps the rendered fragment in a Typst
`#layout(size => …)` block that measures the table and rescales it by a uniform
factor. This is useful when a wide table would otherwise overflow the text
column.

Three knobs control `.theme_resize()`:

- `width` — target width as a fraction of the page content width (`1` = full
  width). Used unless `height` is given.
- `height` — target height as a fraction of the page content height. When set,
  height drives the scaling and width follows proportionally.
- `direction` — `"down"` only shrinks oversized tables, `"up"` only expands
  undersized ones, `"both"` (default) always scales to the target.

```python
from tytable import tt

# Shrink only if wider than 95% of the page; leave smaller tables alone.
tt(df).theme_resize(width=0.95, direction="down")

# Always scale to the full page width.
tt(df).theme_resize()
```

#tag("SOURCE")
#source("examples/12_resize.py")

#tag("RESULT")
#v(0.12em)
#include "build/12_resize.typ"

=== Multipage tables

Typst figures normally keep their contents on one page. For a long table,
`.theme_multipage()` makes tytable figures breakable while preserving their
caption, numbering, label, and reference semantics. The complete header block,
including column-group rows, repeats at the top of each page by default:

```python
tt(df, caption="Long results", label="long-results").theme_multipage()
```

Disable header repetition when the surrounding document supplies its own page
context:

```python
tt(df).theme_multipage(repeat_headers=False)
```

The generated Typst show rule is scoped to figures whose kind is `"tytable"`,
so images and other figures later in the document retain their own page-break
behaviour.


== Images & sparklines

Use `.images()` to embed existing files without Matplotlib or the optional
`images` extra. This standalone example references three committed SVG country
flags. Its paths start with `../assets` because they resolve from the saved
`build/07_static_images.typ` fragment, not from the Python script:

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


== Alternative backends <alternative-backends>

Typst is the primary output format, but a `TyTable` can render the same recorded
intent as HTML or fixed-width terminal text. These backends are useful for
development, tests, and applications that do not need a paged document. They
are independent renderers, not conversions of the generated Typst, so use a
compiled Typst preview for final layout decisions.

=== HTML

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

=== ASCII terminal output

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

=== Backend styling support

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


== Advanced Python: reusable table components

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

=== A report component, end to end

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

=== Design rules for larger programs

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

=== Developing and debugging a table

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

=== Data from a web source

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
