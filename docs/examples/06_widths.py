"""Column-width example — fractions, fixed units, and auto sizing."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Metric": ["Revenue", "Cost", "Profit", "Margin"],
        "Value": [12450.5, 9800.0, 2650.5, 0.21],
        "Note": [
            "Q3 total, excludes rebates",
            "Fixed + variable",
            "After tax",
            "Ratio of profit to revenue",
        ],
    }
)

(
    tt(df, caption="Mixed column widths", width=[0.2, 0.15, None])
    .fmt(j="Value", digits=2)
    .save("build/06_widths.typ")
)
