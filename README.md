# tytable

A small, easy-to-use Python library that turns **Polars DataFrames** into
**Typst tables**, inspired by R's [`tinytable`](https://github.com/vincentarelbundock/tinytable)
package. Most of tinytable's styling power, plus image/sparkline support and a
Jupyter HTML preview.

## Install

```
pip install tytable
pip install tytable[images]   # for .plot() / .images() (matplotlib + numpy)
```

From GitHub with uv:

```
uv pip install git+https://github.com/EinMaulwurf/tytable.git
uv add git+https://github.com/EinMaulwurf/tytable.git   # as a dependency in pyproject.toml
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
    tt(df, caption="Product scores")
    .fmt(j="Score", digits=2)
    .style(j="Score", align="c")
    .style(i=0, bold=True, background="#2c3e50", color="white")
    .save("report_assets/products.typ")
)

# In Jupyter, let `tab` be the last line of a cell to see an HTML preview.
tab
```

The `.typ` file can be `#import`ed into a Typst report and compiled as part of
the whole document.

## Conventions

- **0-based row indexing**: `i=0` is the first data row (the row _after_ the
  column-name header). Use `i="header"` for the column-name row, negative ints
  for column-group header rows (`-1` is the topmost level).
- **Column selection by name**: `j="Score"` (preferred); `j=0` selects the first
  column by position.
- **Method chaining**: `.style()`, `.fmt()`, `.group()`, `.theme()` all return
  `self`. `.render()` / `.save()` are terminal.
- **Lazy evaluation**: styling, formatting, grouping, and plotting are recorded
  as _intent_ and replayed in a fixed order at render time. Row indices always
  refer to the final, visible table.

## Formatting

**Format in polars first; `.fmt()` for the rest.** Most formatting (rounding,
string ops, `fill_null`, percentages) is best done in polars before passing the
dataframe to `tt()`:

```python
df = df.with_columns(
    (pl.col("rate") * 100).round(1).cast(pl.Utf8).alias("pct"),
    pl.col("name").str.to_titlecase(),
)
```

`.fmt()` covers the high-value cases polars can't:

- `digits` — fixed decimal places (`num_fmt="decimal"`) or significant figures
  (`num_fmt="significant"`) for float columns
- `replace` — replace missing/null/NaN values with a string or dict mapping
- `escape` — per-cell Typst escaping (on by default via `tt(escape=True)`)
- `fn` — custom column-wise transformation

```python
tt(df)
    .fmt(j="score", digits=2)
    .fmt(j="status", replace="—")
    .fmt(j="label", fn=lambda vec: [f"[{v}]" for v in vec])
    .save("out.typ")
```

## Styling

```python
tt(df)
    .style(i="header", bold=True, line="b")
    .style(j="Score", align="c")
    .style(i=0, j="Score", color="#c0392b", background="#fdf2e9")
    .style(i=2, italic=True, strikeout=True)
```

Supported properties: `bold`, `italic`, `underline`, `strikeout`, `monospace`,
`smallcaps`, `color`, `background`, `fontsize`, `align` (`l`/`c`/`r`),
`alignv` (`t`/`m`/`b`), `indent`, `colspan`, `rowspan`, and per-side borders
(`line="tblr"`, any combination, with `line_color` / `line_width`).

## Grouping

```python
# Column groups (spanning headers)
tt(df).group(j={"Group A": [0, 1], "Group B": [2, 3]})

# Row groups (separator label rows inserted before a 0-based data row)
tt(df).group(i={"Financial": 0, "Operational": 3})
```

## Themes

Built-in: `default` (booktab rules), `striped`, `grid`, `empty`, `rotate`. Pass
a callable for a custom theme.

```python
tt(df, theme="striped")
tt(df, theme=None).theme("grid")
```

## Images & sparklines

Supply your own plotting function (`fun(values) -> matplotlib Figure`); the
package handles PNG saving and path handling. A `sparkline` example ships in
`examples/sparkline.py`.

```python
from examples.sparkline import sparkline

tt(df).plot(j="Trend", fun=sparkline, height=1.5).save("out.typ")
```

## Asset-path caveat (`#import` workflow)

Because you `#import` the generated `.typ` into a parent report and compile
elsewhere, image paths must resolve relative to your **Typst project root**
(where `typst compile` runs). Make the assets location explicit:

```python
.save("build/tables/products.typ", assets="../assets/products")
```

Images then land in `build/assets/products/` and the `.typ` references
`../assets/products/...`, which resolves correctly from `build/tables/` when
compiled as part of the parent. Without an explicit `assets=`, images land in a
`tytable_assets/` folder next to the output file.

## Coming from R tinytable

| R (`tinytable`)                  | Python (`tytable`)                 |
| -------------------------------- | ----------------------------------- | ------------------------------------- |
| `tt(data)`                       | `tt(df)` (Polars DataFrame)         |
| `style_tt(x, ...)`               | `.style(...)`                       |
| `format_tt(x, ...)`              | `.fmt(...)`                         |
| `group_tt(x, ...)`               | `.group(...)`                       |
| `theme_tt(x, ...)`               | `.theme(...)` / `tt(theme=...)`     |
| `print(x, "typst")`              | `.render("typst")`                  |
| `save_tt(x, "out.typ")`          | `.save("out.typ")`                  |
| `tt(x)                           | > format(...) %>% ...` (pipe)       | `.fmt(...).style(...)` (method chain) |
| 1-based row indexing, 0=colnames | **0-based** data rows; `i="header"` |
| column by integer position       | column by **name** (preferred)      |

## API

### `tt(data, *, caption=None, width=None, gutter=2, colnames=True, escape=True, theme="default", ...)`

Create a `TinyTable` from a Polars DataFrame. `gutter` controls the Typst
column-gutter (in pt when numeric, or a Typst length string like `"0.1em"`);
set to `None` to suppress it entirely.

### `.style(i=None, j=None, *, bold=None, italic=None, ..., line=None)`

Apply cell styling via selectors. Returns `self` for chaining.

### `.fmt(i=None, j=None, *, digits=None, num_fmt="decimal", replace=None, escape=False, fn=None)`

Apply value formatting. Returns `self` for chaining.

### `.group(i=None, j=None)`

Add row groups (`i` dict or list) and column groups (`j` dict or delimiter).

### `.theme(name_or_callable=None)`

Apply a theme (`default`, `striped`, `grid`, `empty`, `rotate`, or a callable).

### `.plot(j, *, fun, data=None, height=1.0, ...)` / `.images(j, *, paths, ...)`

Embed generated plots or existing images. Requires the `images` extra.

### `.render(output="typst")` → `str`

Render the table as a Typst (or `html`/`ascii`) string.

### `.finalize(fn)` → `self`

Register a post-render callback. `fn(rendered_string, output)` receives the
fully rendered string and the output format, and must return the (possibly
modified) string. Chainable; multiple callbacks run in registration order.

```python
tt(df).finalize(lambda s, o: s.replace("5pt", "2pt") if o == "typst" else s)
```

### Column widths

The `width` parameter of `tt()` accepts several forms:

```python
tt(df, width=None)              # all columns auto (default)
tt(df, width=0.8)               # equal percentage across all columns
tt(df, width=[0.3, 0.7])        # per-column fractions → percentages
tt(df, width="5cm")             # Typst/HTML unit for all columns
tt(df, width=["5cm", None])     # first col 5cm, rest auto
tt(df, width=[0.3, None, "2cm"])  # mix fractions, auto, and units
```

### `.save(path, assets=None)`

Save the table to a file (`.typ` or `.html`).
