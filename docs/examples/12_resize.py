"""Resize theme — scale a wide table down to fit the page width."""

import polars as pl

from tytable import tt

# A wide frame whose natural width would overflow the text column.
df = pl.DataFrame(
    {
        "Region": ["North", "South", "East"],
        "Q1": [12450, 9810, 7320],
        "Q2": [13120, 10105, 7980],
        "Q3": [11980, 11240, 8455],
        "Q4": [14250, 12010, 9020],
        "Notes": ["Strong finish", "Recovery", "Growth market"],
    }
)

# direction="down" only shrinks when the table is wider than `width` of the
# page; smaller tables are left untouched. Use direction="both" to always scale.
(
    tt(df, caption='Resized to fit (width=0.95, direction="down")')
    .theme_resize(width=0.95, direction="down")
    .save("build/12_resize.typ")
)
