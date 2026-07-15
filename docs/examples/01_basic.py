"""The smallest complete tytable example."""

import polars as pl

from tytable import tt

data = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo"],
        "Price": [9.99, 14.50, 3.25],
        "In stock": [120, 0, 54],
    }
)

table = tt(data)
table.save("build/01_basic.typ")
