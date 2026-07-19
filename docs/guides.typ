#import "_common.typ": source, tag

#pagebreak()

= — Recipes and advanced topics <advanced-guides>

These chapters are independent. Read the ones that match the table or application you are building.

== Column widths

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
== Images & sparklines

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
== Table showcase

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
