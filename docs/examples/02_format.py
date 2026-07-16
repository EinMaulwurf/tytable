"""Formatting example — numeric, replacement, and Typst math formats."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [12450.5, 9800.0, 15200.25, None],
        "Significant": [3.14159, 0.00123, 987.654, None],
        "Scientific": [3141.59, 0.00123, 987654.0, None],
        "Equation": [
            "e^(i pi) + 1 = 0",
            "sum_(k=1)^n k = n(n+1)/2",
            "integral_0^infinity e^(-x) dif x = 1",
            "mat(1, 2; 3, 4)",
        ],
        "Status": ["active", "active", None, "paused"],
    }
)

(
    tt(df, caption="Regional revenue")
    .fmt(j="Revenue", digits=2)
    .fmt(j="Significant", digits=3, num_fmt="significant")
    .fmt(j="Scientific", digits=2, num_fmt="scientific")
    .fmt(j="Equation", math=True)
    .fmt(j="Revenue", replace={"null": "—"})
    .fmt(j="Status", replace={"null": "n/a"})
    .save("build/02_format.typ")
)
