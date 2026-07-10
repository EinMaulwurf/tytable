"""Minimal tytable example — a plain table from a Polars DataFrame."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo"],
        "Price": [9.99, 14.50, 3.25],
        "In stock": [120, 0, 54],
    }
)

tt(df, caption="Catalog").save("build/01_basic.typ")
