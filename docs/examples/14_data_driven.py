"""Data-driven selectors — style results without fixed row numbers."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [1284, 936, 1512, 1067],
        "Cost": [1150, 980, 1290, 1120],
        "Growth %": [8.2, 3.1, 12.0, -4.5],
        "Profit": [134, -44, 222, -53],
    }
)

(
    tt(df, caption="Regional performance review", width=1)
    .fmt(j=["Revenue", "Cost", "Profit"], digits=0)
    .fmt(j="Growth %", digits=1)
    .style(i="header", bold=True, background="#2c3e50", color="white")
    .style(
        i=(pl.col("Growth %") > 0) & (pl.col("Profit") > 0),
        bold=True,
        color="#087e8b",
    )
    .style(i=pl.Series("review", [False, True, False, True]), background="#fff4cc")
    .style(i=lambda row: row["Profit"] < 0, j="Profit", bold=True, color="#b23a48")
    .save("build/14_data_driven.typ")
)
