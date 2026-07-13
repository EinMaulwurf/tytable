"""
Renaming columns with ``.set_name()`` — display names without touching polars.

Polars column names are identifiers, so they cannot be empty strings, must be
unique, and disallow some characters. ``.set_name()`` renames columns for
display only — the underlying DataFrame is never modified — so you can use
any header you like, including ``""``, duplicates, or names that would be
awkward as polars column names.

Two calling modes:

1. *Per-column*: ``.set_name(j, name=...)`` renames the column(s) selected by
   ``j`` (same selectors as ``.style()`` / ``.fmt()``: name, integer position,
   or a list; pass ``regex=True`` for regex patterns). ``name`` is a single ``str`` applied to every match, or a
   ``list[str]`` with one entry per matched column.
2. *Full-list replace*: ``.set_name(name=[...])`` (omit ``j``) replaces every
   column header at once — the list length must equal the column count.

After renaming, subsequent ``j`` selectors use the *new* display names. The
example below starts from machine-friendly column names (``grp``, ``val_1``,
``val_2``) and replaces them with human-readable headers — including an empty
string for the grouping column, whose entries are self-describing.
"""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "grp": ["North", "South", "East", "West"],
        "val_1": [12450.5, 9800.0, 15200.25, 7300.75],
        "val_2": [8100.0, 6200.0, 9900.0, 5100.0],
    }
)

(
    tt(df, caption="Renaming columns for display", width=1)
    .set_name(name=["", "Revenue", "Cost"])
    .fmt(j=["Revenue", "Cost"], digits=2)
    .style(i="header", bold=True, background="#2c3e50", color="white")
    .style(j=["Revenue", "Cost"], align="r")
    .save("build/15_set_name.typ")
)
