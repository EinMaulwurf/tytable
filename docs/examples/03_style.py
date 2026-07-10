"""Styling example — typography, colour, alignment, and per-side borders."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Sales": [12450.5, 9800.0, 15200.25, 7300.75],
        "Growth": [0.12, -0.04, 0.21, 0.08],
    }
)

(
    tt(df, caption="Quarterly sales by region")
    .fmt(j="Sales", digits=2)
    .fmt(j="Growth", digits=2)
    .style(i="header", bold=True, color="white", background="#2c3e50", line="b")
    .style(j=["Sales", "Growth"], align="r")
    .style(i=2, bold=True, color="#27ae60")
    .style(i=1, color="#c0392b")
    .style(i=0, line="b", line_color="#bdc3c7")
    .style(line="lr", line_width=0.05)
    .save("build/03_style.typ")
)
