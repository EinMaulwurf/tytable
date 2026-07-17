"""Intersect a cell mask with row and column restrictions.

The ``Active`` column supplies a row mask through ``i``. ``j`` limits the
candidate display columns, and ``where`` tests each candidate cell's own value.
A cell is highlighted only when all three selectors include it.
"""

import polars as pl
import polars.selectors as cs

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["A", "B", "C"],
        "Active": [True, False, True],
        "Price": [150, 180, 80],
        "Stock": [20, 200, 240],
    }
)

(
    tt(df, caption="Over 100, but only in active rows")
    .style(
        i=pl.col("Active"),
        j=["Price", "Stock"],
        where=cs.numeric() > 100,
        bold=True,
        background="#d7f0ea",
    )
    .style(i="header", bold=True, background="#17324d", color="white")
    .save("build/19_cell_where_active.typ")
)
