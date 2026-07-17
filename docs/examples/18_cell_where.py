"""Cell-level styling — test each numeric cell instead of selecting whole rows.

``i`` and ``j`` select rows and columns independently, so their intersections
form a rectangle. ``where`` instead keeps the shape of a multi-column Polars
expression and styles only the individual cells whose mask value is true.
"""

import polars as pl
import polars.selectors as cs

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["A", "B"],
        "Price": [150, 80],
        "Stock": [20, 200],
    }
)

(
    tt(df, caption="Only numeric cells over 100 are highlighted")
    .style(where=cs.numeric() > 100, bold=True, background="#d7f0ea")
    .style(i="header", bold=True, background="#17324d", color="white")
    .save("build/18_cell_where.typ")
)
