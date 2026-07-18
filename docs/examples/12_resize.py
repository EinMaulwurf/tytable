"""Resize a wide table down to fit the page width."""

import polars as pl

from tytable import tt

# A wide frame whose natural width would overflow the text column.
df = pl.DataFrame(
    {
        "Region": ["North", "South", "East"],
        "Product category": ["Enterprise", "Consumer", "Public sector"],
        "January revenue": [12450, 9810, 7320],
        "February revenue": [13120, 10105, 7980],
        "March revenue": [11980, 11240, 8455],
        "April revenue": [14250, 12010, 9020],
        "May revenue": [15110, 12640, 9440],
        "June revenue": [15890, 13120, 9870],
        "Forecast status": ["Above target", "On track", "Above target"],
        "Commentary": ["Strong finish", "Recovery continuing", "Growth market"],
    }
)

# direction="down" only shrinks when the table is wider than `width` of the
# page; smaller tables are left untouched. Use direction="both" to always scale.
(
    tt(df, caption='Resized to fit (width=0.95, direction="down")')
    .resize(width=0.95, direction="down")
    .save("build/12_resize.typ")
)
