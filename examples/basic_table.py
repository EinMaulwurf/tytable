"""Minimal tytable example — a plain table saved to Typst.

Run:  uv run python examples/basic_table.py
"""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo"],
        "Price": [9.99, 14.50, 3.25],
        "In stock": [120, 0, 54],
    }
)

out = tt(df, caption="Catalog").render("typst")
print(out)
