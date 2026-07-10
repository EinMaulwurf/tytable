"""Formatting example — digits, replacements, and the polars-first philosophy."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [12450.5, 9800.0, 15200.25, None],
        "Status": ["active", "active", None, "paused"],
    }
)

(
    tt(df, caption="Regional revenue")
    .fmt(j="Revenue", digits=2)
    .fmt(j="Revenue", replace={"null": "—"})
    .fmt(j="Status", replace={"null": "n/a"})
    .save("build/02_format.typ")
)
