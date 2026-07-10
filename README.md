# tinytables

A Python library for turning Polars DataFrames into Typst tables.

## Quickstart

```python
import polars as pl
from tinytables import tt

df = pl.DataFrame({"x": [1.0, 2.0, 3.0], "y": ["a", "b", "c"]})

tt(df).style(bold=True).save("table.typ")
```

## Formatting

**Format in polars first; `.fmt()` for the rest.** Most formatting (rounding, string
ops, fill_null, percentages) is best done in polars before passing the dataframe
to `tt()`:

```python
df = df.with_columns(
    (pl.col("rate") * 100).round(1).cast(pl.Utf8).alias("pct"),
    pl.col("name").str.to_titlecase(),
)
```

`.fmt()` covers the high-value cases polars can't handle:

- `digits` — fixed decimal places or significant figures for float columns
- `replace` — replace missing/null/NaN values with a string or dict mapping
- `escape` — per-cell Typst escaping (honoured by default via `tt(escape=True)`)
- `fn` — custom column-wise transformation

```python
tt(df)
    .fmt(j="score", digits=2)
    .fmt(j="status", replace="—")
    .fmt(j="label", fn=lambda vec: [f"[{v}]" for v in vec])
    .save("out.typ")
```

## API

### `tt(data, *, caption=None, width=None, colnames=True, escape=True, ...)`

Create a `TinyTable` from a Polars DataFrame.

### `.style(i=None, j=None, *, bold=None, italic=None, ...)`

Apply cell formatting via selectors. Returns `self` for chaining.

### `.group(i=None, j=None)`

Add row groups (dict or list) and column groups (dict or delimiter string).

### `.fmt(i=None, j=None, *, digits=None, num_fmt="decimal", replace=None, escape=False, fn=None)`

Apply value formatting. Returns `self` for chaining.

### `.render(output="typst")`

Render the table as a Typst string.

### `.save(path)`

Save the table to a file (`.typ` or `.html`).
