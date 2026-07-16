"""
Full report example — combining groups, formatting, styling, and widths.

A feature-rich table built without any image dependencies: explicit column
groups (dict form), a row-group separator, numeric formatting, a full-width
layout, and targeted styling. Numeric alignment follows the source dtypes.
"""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Store": ["01 Downtown", "02 Midtown", "03 Harborside", "04 Eastside"],
        "Q1 Rev": [12450.5, 9800.0, 15200.25, 7300.75],
        "Q1 Cost": [8100.0, 6200.0, 9900.0, 5100.0],
        "Q2 Rev": [13100.0, 9600.0, 16050.5, 7900.0],
        "Q2 Cost": [8300.0, 6000.0, 10100.0, 5400.0],
    }
)

(
    tt(df, caption="Store performance summary", width=1)
    .group(j={"Q1": ["Q1 Rev", "Q1 Cost"], "Q2": ["Q2 Rev", "Q2 Cost"]})
    .group(i={"Coastal district": 2})
    .fmt(j=["Q1 Rev", "Q1 Cost", "Q2 Rev", "Q2 Cost"], digits=2)
    .style(i="header", bold=True, color="white", background="#2c3e50")
    .style(i="groupj", bold=True, background="#ecf0f1")
    .style(i="groupi", bold=True, background="#f0f0f0")
    .style(j="Store", bold=True)
    .style(i=0, background="#fdf2e9")
    .save("build/08_full_report.typ")
)
