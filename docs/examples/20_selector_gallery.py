"""Compact selector gallery used by the documentation."""

from collections.abc import Callable

import polars as pl
import polars.selectors as cs

from tytable import TyTable, tt

df = pl.DataFrame(
    {
        "Item": ["A", "B", "C", "D"],
        "Sales": [80, 120, 140, 90],
        "Cost": [110, 70, 130, 60],
        "Score": [95, 105, 85, 125],
    }
)


def base_table() -> TyTable:
    return (
        tt(df, figure=False, width=1)
        .group(j={"Results": ["Sales", "Cost", "Score"]})
        .group(i={"Group B": 2})
        .theme_grid()
        .style(i=["header", "groupi", "groupj"], bold=True)
    )


examples: list[tuple[str, Callable[[TyTable], TyTable]]] = [
    ("i0", lambda table: table.style(i=0, background="#c6efce")),
    ("ilist", lambda table: table.style(i=[0, 2], background="#c6efce")),
    (
        "iexpr",
        lambda table: table.style(i=pl.col("Score") > 100, background="#c6efce"),
    ),
    ("jname", lambda table: table.style(j="Sales", background="#c6efce")),
    (
        "ij",
        lambda table: table.style(i=1, j=["Sales", "Cost"], background="#c6efce"),
    ),
    (
        "crossproduct",
        lambda table: table.style(
            i=pl.col("Score") > 100,
            j=["Sales", "Cost"],
            background="#c6efce",
        ),
    ),
    (
        "where",
        lambda table: table.style(where=cs.numeric() > 100, background="#c6efce"),
    ),
    ("header", lambda table: table.style(i="header", background="#c6efce")),
    (
        "groups",
        lambda table: table.style(i=["groupi", "groupj"], background="#c6efce"),
    ),
]

for name, apply_selection in examples:
    apply_selection(base_table()).save(f"build/20_selector_{name}.typ")
