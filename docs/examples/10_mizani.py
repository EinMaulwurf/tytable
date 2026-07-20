"""Mizani formatters — scales-style currency and percentage labels."""

import polars as pl
from mizani.labels import label_currency, label_percent

from tytable import tt

currency_label = label_currency(prefix="$", precision=0, big_mark=",")
percent_label = label_percent(precision=1)


def format_currency(values: list[int]) -> list[str]:
    """Apply Mizani's numeric label callable to the typed column."""

    return list(currency_label(values))


def format_percent(values: list[float]) -> list[str]:
    """Apply Mizani's numeric label callable to the typed column."""

    return list(percent_label(values))


data = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [1_284_000, 936_000, 1_512_000, 1_067_000],
        "Margin": [0.128, -0.064, 0.173, 0.091],
    }
)

(
    tt(data, caption="Labels formatted with Mizani")
    .fmt(j="Revenue", fn=format_currency, fn_values="typed")
    .fmt(j="Margin", fn=format_percent, fn_values="typed")
    .fmt(j=["Revenue", "Margin"], escape=True)
    .save("build/10_mizani.typ")
)
