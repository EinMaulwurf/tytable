"""
Data-driven row selectors — style rows based on cell values.

Instead of hard-coding row numbers, use a Polars expression, a boolean
``pl.Series``, or a Python callable to select rows dynamically. The selector is
evaluated against the original DataFrame at render time, so it stays correct
even when the data changes.

This example demonstrates all three forms:
1. ``pl.col("Score") > 80`` — a polars expression (selects Alice and Charlie)
2. A boolean ``pl.Series`` mask — explicit True/False per row
3. A ``lambda row: ...`` — a pure-Python predicate on the named row dict
"""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Student": ["Alice", "Bob", "Charlie", "Diana"],
        "Score": [95, 72, 88, 60],
        "Grade": ["A", "C", "B", "D"],
    }
)

(
    tt(df, caption="Data-driven row selectors", width=1)
    .fmt(j=["Score"], digits=0)
    .style(i="header", bold=True, background="#2c3e50", color="white")
    .style(i=pl.col("Score") > 80, bold=True)          # polars expression
    .style(i=pl.Series("m", [False, True, False, False]), italic=True)  # boolean series
    .style(i=lambda row: row["Grade"] == "D", color="#c0392b")          # callable
    .save("build/14_data_driven.typ")
)
