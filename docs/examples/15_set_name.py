"""
Renaming columns with ``.set_name()``.
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
