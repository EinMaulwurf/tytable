"""A first report-ready table: format, style, caption, and label."""

import polars as pl

from tytable import tt

data = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo"],
        "Price": [9.99, 14.50, 3.25],
        "In stock": [120, 0, 54],
    }
)

(
    tt(data, caption="Product catalog", label="product-catalog")
    .fmt(j="Price", digits=2)
    .style(i="header", bold=True, background="#17324d", color="white")
    .save("build/tables/catalog.typ")
)
