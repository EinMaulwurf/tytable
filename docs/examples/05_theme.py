"""Themes gallery — every built-in theme applied to the same data."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "City": ["Berlin", "Paris", "Rome", "Madrid"],
        "Pop. (M)": [3.85, 2.16, 2.87, 3.32],
        "Area (km²)": [891, 105, 1285, 604],
    }
)

tt(df, caption="default theme").save("build/05_theme_default.typ")
tt(df, caption="striped theme").theme_striped().save("build/05_theme_striped.typ")
tt(df, caption="grid theme").theme_grid().save("build/05_theme_grid.typ")
tt(df, caption="plain theme").theme_plain().save("build/05_theme_plain.typ")
