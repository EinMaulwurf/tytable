"""Grouped table example — spanning column headers and row-group separator rows.

Run:  uv run python examples/grouped_table.py
"""

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

out = (
    tt(df, caption="Half-year financials")
    # Column groups derived from the "_" delimiter in column names.
    .group(j="_")
    # Row-group separator label inserted before 0-based data row 1.
    .group(i={"Division B": 1})
    .style(i="groupi", bold=True, background="#f0f0f0")
    .render("typst")
)
print(out)
