# tytable coding guide for agents

This is a compact reference for coding assistants that need to write `tytable` code without prior knowledge of the package. It covers the common public API and the selection, styling, and formatting rules that are easiest to get wrong. For edge cases, consult the public docstrings in `src/tytable/_tytable.py` and the complete rendered manual built from `docs/main.typ`.

`tytable` turns a Polars `DataFrame` into a Typst table. It can also render HTML previews and a plain ASCII representation. Import core objects from `tytable` and selector factories from `tytable.selectors`:

```python
import polars as pl
from tytable import NoteDict, TyTable, tt
from tytable.selectors import colgroup, groupi, groupj, regex, rowgroup
```

Use `tt(df)` to construct tables. `TyTable` is mainly useful as a type annotation, and `NoteDict` describes targeted notes. Do not import private modules or construct internal directive classes.

## Mental model

Calls such as `.fmt()`, `.style()`, and `.group()` record intent. They do not immediately rewrite a rendered grid. The intent is resolved when `.render()` or `.save()` is called, after all groups and structural rows are known.

```python
table: TyTable = (
    tt(df, caption="Quarterly results", label="quarterly-results")
    .fmt(j="Revenue", digits=2)
    .style(i="header", bold=True, background="#17324d", color="white")
    .theme_striped()
)

typst_source: str = table.render()
table.save("build/quarterly-results.typ")
```

Configuration methods mutate the table and return `self`, so they can be chained. `.render()` returns a string and `.save()` returns `None`; both are terminal operations. The same table may be rendered or saved repeatedly.

Use `.clone()` to derive independently configurable variants from one table; callback and selector objects are reused by reference.

Prefer doing substantial data manipulation in Polars before calling `tt()`. Use `.fmt()` for presentation-time value transformations and `.style()` for appearance.

## Creating a table

The common constructor options are:

```python
tt(
    df,
    figure=True,
    caption=None,
    label=None,
    notes=None,
    width=None,
    height=None,
    gutter=2,
    column_gutter=None,
    row_gutter=None,
    colnames=True,
    escape=True,
)
```

- `df` must be a Polars `DataFrame`. It is cloned on construction.
- `caption` and `label` require `figure=True`, which is the default.
- `width=1` fills the available line. A list sets widths per column and may mix fractions, Typst lengths such as `"3cm"` or `1fr`, and `None` for automatic width.
- `height` is the row height in `em`, not a table scaling factor.
- `gutter` retains the legacy grouped-table column spacing. Set `column_gutter` or `row_gutter` for explicit Typst track spacing; numbers are points and strings are Typst lengths.
- `escape=True` safely escapes cell text for the output backend. Disable it only when intentionally supplying raw markup.

## Row and column selectors

`.style()`, `.fmt()`, `.plot()`, `.images()`, and targeted `NoteDict` entries use `i` for rows and `j` for columns. `.style()`, `.fmt()`, and targeted notes also accept `where` for individual data cells.

### Rows: `i`

Public integer row positions are always zero-based positions in the original source DataFrame:

```python
table.style(i=0, bold=True)        # first source-data row
table.style(i=[0, 2], bold=True)   # first and third source-data rows
table.style(i=range(5), bold=True) # first five source-data rows
```

Inserted row-group separators do not change what `i=0`, `i=1`, and so on mean. Negative row indices are not supported.

Semantic row names are:

| Selector | Meaning |
| --- | --- |
| omitted, `None`, or `"data"` | all genuine source-data rows |
| `"header"` | the column-name row |
| `"groupi"` or `groupi()` | all inserted row-group separator rows |
| `groupi(label="A")` | every row-group separator with the exact registered label `"A"` |
| `rowgroup(label="A")` | source-data rows belonging to every row group labelled `"A"` |
| `"groupj"` or `groupj()` | all spanning column-group header rows |
| `groupj(level=n)` | one nested column-group header level; level 0 is first-created and innermost |
| `"all"` | the complete displayed grid |
| `"caption"` | the caption; supported only by `.style()` |
| `"notes"` | note text; supported only by `.style()` |

Import `groupi`, `rowgroup`, and `groupj` from `tytable.selectors` for typed group selection. `groupi(label="A")` selects every row-group separator whose original registered label is exactly `"A"`, while `rowgroup(label="A")` selects the source-data rows after each matching separator up to the next separator. Repeated labels all match, later formatting of the displayed label does not change selection, and a missing label raises `ValueError`. Repeated `.group(j=...)` calls create nested header levels: the first call is level 0 nearest the ordinary column names, and each later call adds the next outer level above it. On a selected group-header level, `j` identifies the spanning cell covering the chosen original source column. Selecting several member columns covered by the same header styles that cell once. A hidden member column does not select a group cell that survives over another visible member, and a level removed entirely by `.show_columns()` remains absent rather than renumbering another level.

Sequences may mix integer and semantic selectors, including `groupi(label=...)`, `rowgroup(label=...)`, and `groupj(level=...)`. Targeted notes put the ordinary row selectors, including `groupi(...)` and `rowgroup(...)`, in a `NoteDict` passed to `tt(..., notes=[...])`; typed `groupj()` selectors are styling-only. Not every operation supports every structural row: `.style()` supports the full grid plus captions and notes; `.fmt()` and targeted notes support data, `"header"`, and `"groupi"`; `.plot()` and `.images()` support data and `"groupi"`. Unsupported selections raise an error during rendering.

Rows can also be selected from source values:

```python
table.style(i=pl.col("Score") > 80, bold=True)
table.style(i=pl.Series([True, False, True]), bold=True)
table.style(i=lambda row: row["Region"] == "North", bold=True)
```

Boolean masks must have exactly one Boolean value per source row. Expressions and callables are evaluated against the original DataFrame. These forms also work as the `i` value in a targeted `NoteDict`.

### Columns: `j`

Prefer exact original DataFrame names:

```python
table.fmt(j="Revenue", digits=2)
table.style(j=["Revenue", "Cost"], align="r")
table.style(j=0, bold=True)  # positions are supported but less readable
```

Omitting `j` selects every column. Names are case-sensitive. A sequence may contain names, integer positions, `regex(pattern)`, `colgroup(label=..., level=...)`, and Polars selectors. All resolve against the original DataFrame schema and work anywhere `j` selects columns, including `.set_name()`, `.show_columns()`, targeted notes, and later column-group values. `colgroup` matches every registered group with the exact label at the required stable level and combines their source columns; missing labels or levels raise `ValueError`. `regex(pattern)` uses Python `re.search`, limits patterns to 500 characters, and raises `ValueError` for an invalid pattern or no matches. Polars selectors such as `cs.numeric()`, `cs.string()`, `cs.starts_with(...)`, `cs.by_dtype(...)`, and `cs.matches(...)` produce an empty selection when nothing matches; column groups still require a nonempty contiguous result.

```python
import polars.selectors as cs
from tytable.selectors import colgroup, regex

table.fmt(j=regex(r"^(Revenue|Cost)$"), digits=0)
table.style(j=["Total", regex(r"^Q")], bold=True)
table.fmt(j=cs.numeric(), digits=2)
table.fmt(j=colgroup(label="Results", level=0), digits=1)
table.show_columns(cs.matches(r"^(Revenue|Cost)$"))
```

Use `.show_columns(j, invert=False)` to choose which source columns are rendered without modifying the DataFrame. It accepts the same names, positions, regex selectors, column-group selectors, Polars selectors, and mixed sequences as other `j` arguments, always preserves source-column order, and replaces any previous display projection. With `invert=True`, the selected columns are omitted. Hidden columns remain available to row expressions, `where`, and other directives:

```python
table = (
    tt(df)
    .style(i=pl.col("warning"), j="name", color="red")
    .show_columns(["name", cs.numeric()])
)
table.show_columns(["warning", cs.starts_with("_")], invert=True)
```

Display names created by `.set_name()` never become selectors. Continue to select the original name:

```python
table = tt(df).set_name(j="annual_revenue_usd", name="Revenue")
table.fmt(j="annual_revenue_usd", digits=0)  # correct
```

Rename the Polars DataFrame first if a friendly name should become the true selector name.

### Individual cells: `where`

Use `where` with `.style()`, `.fmt()`, or a targeted `NoteDict` when the condition differs cell by cell:

```python
import polars.selectors as cs

table.style(where=cs.numeric() > 100, bold=True, background="#d7f0ea")
table.fmt(j=["Revenue", "Cost"], where=cs.numeric() >= 1_000, digits=0)
high_values = NoteDict(text="Value exceeds 100", where=cs.numeric() > 100)
table = tt(df, notes=[high_values])
```

The expression is evaluated on the original typed DataFrame. Its Boolean output columns are matched to source columns by name and intersected with any `i` and `j` selection. `where` cannot target headers, group rows, captions, or notes.

### Combining `i`, `j`, and `where`

Using both `i` and `j` selects their rectangular cross-product. Adding `where` intersects that rectangle with the cells where the expression is true:

```python
table.style(i=pl.col("Active"), j=["Revenue", "Cost"], where=cs.numeric() > 100, bold=True)
```

## Styling

Use `.style(i=..., j=..., ...)` for appearance. Combine properties that share selectors in one call:

```python
table.style(
    i="header",
    bold=True,
    color="white",
    background="#2c3e50",
    align="c",
    line="b",
    line_color="#17202a",
)
```

Common style properties are:

| Property | Values or units |
| --- | --- |
| `bold`, `italic`, `underline`, `strikeout` | `bool` |
| `monospace`, `smallcaps` | `bool` |
| `color`, `background` | named color or hex string |
| `fontsize` | non-negative number in `em` |
| `align` | `"l"`, `"c"`, or `"r"` |
| `alignv` | `"t"`, `"m"`, or `"b"` |
| `indent` | non-negative number in `em` |
| `padding` | number, `(vertical, horizontal)`, or `(top, right, bottom, left)` in `em` |
| `rotate` | angle in degrees for selected cell content |
| `colspan`, `rowspan` | positive integer span |
| `line` | any combination of `"t"`, `"b"`, `"l"`, and `"r"` |
| `line_style` | `"solid"`, `"dashed"`, `"dotted"`, `"dash-dotted"`, or `"none"` |
| `line_color` | named color or hex string |
| `line_width` | number in `em`; default `0.1` |
| `output` | backend tuple such as `("typst",)` |

Text columns default to left alignment and numeric columns to right alignment. Their headers use the same dtype-aware defaults. Explicit styles override the defaults. When `j` selects several columns, `align` and `alignv` can assign one character per selected column:

```python
table.style(j=["Product", "Revenue", "Growth"], align="lrr")
```

Later style directives override earlier directives where their selected cells and properties overlap. Themes define the replaceable base appearance; explicit styles remain in effect:

```python
table.theme_default()  # booktab-style default
table.theme_plain()
table.theme_striped()
table.theme_grid()
```

Use `.style(i="header", rotate=90)` to rotate header content. `.rotate(90)` rotates the complete table instead.

## Formatting

Use `.fmt(i=..., j=..., ...)` to change displayed values while retaining the source DataFrame and its dtypes:

```python
table = (
    tt(df)
    .fmt(j="Revenue", digits=2)
    .fmt(j="Estimate", digits=3, num_fmt="significant")
    .fmt(j="Measurement", digits=2, num_fmt="scientific")
    .fmt(j="Revenue", replace={"null": "—"})
)
```

Formatting options are:

| Option | Meaning |
| --- | --- |
| `digits` | non-negative integer; format numeric values |
| `num_fmt` | `"decimal"`, `"significant"`, or `"scientific"` |
| `fn` | column-wise callback returning a sequence of the same length |
| `fn_values` | callback input: original `"typed"` values (default) or current `"display"` strings |
| `replace` | `True` blanks missing values, a string fills them, or a dict maps values |
| `linebreak` | literal marker replaced by a native Typst/HTML line break |
| `math` | wrap values in Typst math delimiters; no effect in HTML/ASCII |
| `escape` | escape selected text after the other transforms |
| `output` | backend tuple such as `("typst",)` |

Within one directive, transforms run in this order:

1. `digits`
2. `fn`
3. `replace`
4. `linebreak`
5. `math`
6. `escape`

Decimal formatting uses `digits` places after the decimal point. Significant formatting uses that many significant figures. Scientific formatting uses that many places after the mantissa's decimal point. Numeric source columns remain right-aligned because alignment is inferred from the original dtype.

The `fn` callback is column-wise, not cell-wise. By default it receives the original Python values from the DataFrame for each selected column and must return a non-string sequence of the same length:

```python
def add_percent(values: list[float]) -> list[str]:
    return [f"{100 * value:.1f}%" for value in values]

table.fmt(j="Share", fn=add_percent)
```

Callback results are covered by the default table-wide escaping. Use `.fmt(escape=True)` only to escape selected cells when the table was constructed with `tt(escape=False)`.

Set `fn_values="display"` when a callback should consume the current display strings, including values produced by an earlier formatting directive:

```python
table.fmt(j="Share", digits=2).fmt(j="Share", fn=lambda values: [f"{value}%" for value in values], fn_values="display")
```

Typed callback input cannot be combined with `digits` in the same `.fmt()` call because `digits` produces display strings. Set `fn_values="display"` explicitly when combining them in one directive.

For common typed formats, import `number`, `currency`, `percent`, `date`, `duration`, or `unit` from `tytable.formatters`. Pass the configured formatter to `fn`. For example, `table.fmt(j="Share", fn=percent(digits=1))` converts `0.6281` to `62.8%`. Use `number(digits=1, scale=1 / 1e6)` to display values in millions. The `number`, `currency`, and `unit` formatters use `scale=1` by default. The `percent` formatter uses `scale=100`. These built-ins are factories. Each factory returns the callback that `fn` requires. Pass a custom callback directly as `fn=my_formatter`. Use `fn=my_formatter(...)` only when the custom callback is also a factory. `locale="de_DE"` produces German separators. Semantic formatters cannot be combined with `digits` in the same directive.

For transformations that need several columns at once or aggregation, modify the Polars DataFrame before constructing the table instead.

## Grouping and display names

Insert labelled row separators before stable source rows:

```python
table.group(i={"North": 0, "South": 4})
```

Alternatively, pass one group value per source row; a separator is inserted when the value changes:

```python
table.group(i=["North", "North", "South", "South"])
```

Add spanning column headers with a mapping from labels to original columns:

```python
table.group(j={"Financial": ["Revenue", "Cost"], "Outcome": ["Score"]})
```

`.group(delimiter="_")` can derive hierarchical headers by splitting every original column name on the same literal delimiter.

Rename headers for display without altering selectors:

```python
table.set_name(j="annual_revenue_usd", name="Revenue")
table.set_name(name=["Region", "Revenue", "Cost"])
table.set_name(name={"annual_revenue_usd": "Revenue", "annual_cost_usd": "Cost"})
```

## Notes, layout, and output

Plain strings create untargeted notes. A `NoteDict` can attach a marker to cells selected by `i`, `j`, and `where` using the same semantics as `.fmt()` and `.style()`; put `regex(pattern)` directly in `j` when needed:

```python
note: NoteDict = {
    "text": "Statistically significant",
    "marker": "*",
    "i": [0, 2],
    "j": "Estimate",
}
table = tt(df, notes=[note, "Source: model output"])
```

Useful layout methods include:

```python
table.resize(width=0.95, direction="down")  # scale Typst output down if needed
table.multipage(repeat_headers=True)         # allow page breaks and repeat headers
table.rotate(90)                             # rotate the complete table
```

Render directly or save a fragment:

```python
typst = table.render()          # same as table.render("typst")
html = table.render("html")
ascii_text = table.render("ascii")

table.save("build/table.typ")
table.save("build/table.html") # suffix selects HTML
```

With the Typst CLI installed, `.compile("build/table.pdf")` writes PDF, PNG, or SVG without changing the text-only `.render()` contract. Static images are embedded by default; `root=`, `font_paths=`, `pages=`, and PNG-only `ppi=` expose the relevant compiler controls.

In Jupyter, leaving the table as the last expression displays its HTML preview. `print(table)` uses the ASCII renderer, which displays a zero-column DataFrame as `(empty table)`. A saved `.typ` fragment can be included in a Typst report with `#include`.

`.plot()` generates plots during rendering and requires the optional `images` dependencies. `.images()` embeds or references existing files and does not require that extra. See their public docstrings or the full manual before generating media code because cell cardinality and asset-policy rules are intentionally strict.

## Common mistakes

- Do not use 1-based row positions. `i=0` is the first source row.
- Do not adjust row positions after grouping. Integer selectors always address source rows.
- Do not use negative row positions.
- Do not select a display label introduced by `.set_name()`; use the original DataFrame column name.
- Do not put value options such as `digits` in `.style()`; use `.fmt()`.
- Do not assume `.fmt(fn=...)` is called once per cell; it receives a whole column of original typed values by default, or current strings with `fn_values="display"`.
- Do not use `"left"`, `"center"`, or `"right"` for `align`; use `"l"`, `"c"`, or `"r"`.
- Do not use `where` for structural rows; it selects body cells only.
- Do not disable escaping merely to use `math=True` or `linebreak`; those features cooperate with safe escaping.
- Remember that directives are lazy. Many invalid selectors and incompatible structural targets are reported by `.render()` or `.save()`, not when `.style()` or `.fmt()` is called.
- `.set_name()`, `.show_columns()`, and `.group(j=...)` resolve their column selectors immediately. Register a column group before using `colgroup(...)` with one of these methods.

When uncertain, preserve the source DataFrame, prefer column names over positions, use separate `.fmt()` and `.style()` calls, and render once while developing so lazy validation runs.
