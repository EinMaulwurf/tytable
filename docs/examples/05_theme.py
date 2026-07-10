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

for theme in ["default", "striped", "grid", "empty"]:
    tt(df, theme=theme, caption=f"theme = {theme!r}").save(f"build/05_theme_{theme}.typ")
