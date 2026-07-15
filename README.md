# tytable

A small Python library that turns **Polars DataFrames** into **Typst tables**,
inspired by R's [`tinytable`](https://github.com/vincentarelbundock/tinytable)
package. Most of tinytable's styling power, plus image/sparkline support and a
Jupyter HTML preview.

## Install

Install the latest release from [PyPI](https://pypi.org/project/tytable/):

```
uv add tytable
```

Or with pip:

```
pip install tytable
```

For plots, sparklines, and embedded images, install the optional extra:

```
uv add "tytable[images]"
```

For development (clone and):

```
uv sync --all-extras
make test
```

## Quickstart

```python
import polars as pl
from tytable import tt

df = pl.DataFrame({
    "Product": ["A", "B", "C"],
    "Score": [85.43, 72.10, 91.87],
})

tab = (
    tt(df, caption="Product scores", label="product-scores")
    .fmt(j="Score", digits=2)
    .style(j="Score", align="c")
    .style(i=0, bold=True, background="#2c3e50", color="white")
)

# Save in a script, or let `tab` be the last line of a Jupyter cell for a preview.
tab.save("report_assets/products.typ")
tab
```

The `.typ` file can be `#include`d in a Typst report and compiled as part of the
whole document.

## Conventions

- **0-based row indexing**: `i=0` is the first data row (the row _after_ the
  column-name header). Use `i="header"` for the column-name row, negative ints
  for column-group header rows (`-1` is the innermost row, immediately above
  the column-name header; increasingly negative values move upward).
- **Column selection by name**: `j="Score"` (preferred); `j=0` selects the first
  column by position.
- **Method chaining**: `.style()`, `.fmt()`, `.group()`, `.theme()` all return
  `self`. `.render()` / `.save()` are terminal.
- **Lazy evaluation**: styling, formatting, grouping, and plotting are recorded
  as _intent_ and replayed in a fixed order at render time. Row indices always
  refer to the final, visible table.
- **Figure wrapping**: Typst tables are figures by default, enabling captions,
  numbering, and labels such as `label="product-scores"`. Use `figure=False`
  for an unnumbered table; captions and labels cannot be combined with it.

## Documentation

Full documentation with **rendered examples** (source + result side-by-side),
the complete **API reference**, and an R-tinytable comparison table live in the
PDF built from [`docs/main.typ`](docs/main.typ):

- **Always-current build (HEAD):** <https://einmaulwurf.github.io/tytable/>
- **Versioned (latest release):**
  <https://github.com/EinMaulwurf/tytable/releases/latest/download/tytable-docs.pdf>

Build locally (requires the `typst` CLI):

```
make docs
# → docs/tytable-docs.pdf
```

## Coming from R tinytable

`tt(df)` ↔ `tt(data)`, `.style()` ↔ `style_tt()`, `.fmt()` ↔ `format_tt()`,
`.group()` ↔ `group_tt()`, `.theme()` ↔ `theme_tt()`. Indexing is **0-based**
(vs R's 1-based) and columns are selected by **name** (preferred). The full
comparison table is in the PDF above.
