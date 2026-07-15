"""Grouping example — spanning column headers and row-group separator rows."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Q1_revenue": [100, 200],
        "Q1_cost": [40, 80],
        "Q2_revenue": [120, 220],
        "Q2_cost": [50, 90],
    }
)

(
    tt(df, caption="Half-year financials")
    .group(delimiter="_")
    .group(i={"Division B": 1})
    .style(i="groupi", bold=True, background="#f0f0f0")
    .save("build/04_group.typ")
)
