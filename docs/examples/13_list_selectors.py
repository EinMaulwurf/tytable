"""List selectors — targeting multiple rows and columns by name in one call."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo", "Thing"],
        "Revenue": [12450.5, 9800.0, 15200.25, 7300.75],
        "Cost": [8100.0, 6200.0, 9900.0, 5100.0],
        "Growth %": [12.3, -3.1, 18.7, 5.2],
    }
)

(
    tt(df, caption="List selectors — strings as row/column targets", width=1)
    .style(i=["header", "data"], bold=True)
    .fmt(j=["Revenue", "Cost"], digits=0)
    .fmt(j=["Growth %"], digits=1)
    .style(i="header", background="#2c3e50", color="white")
    .save("build/13_list_selectors.typ")
)
