"""Mizani formatters — scales-style currency and percentage labels."""

import polars as pl
from mizani.labels import label_currency, label_percent

from tytable import tt

currency_label = label_currency(prefix="$", precision=0, big_mark=",")
percent_label = label_percent(precision=1)


def format_currency(values: list[str]) -> list[str]:
    """Adapt tytable's string column to Mizani's numeric label callable."""

    return list(currency_label([float(value) for value in values]))


def format_percent(values: list[str]) -> list[str]:
    """Adapt tytable's string column to Mizani's numeric label callable."""

    return list(percent_label([float(value) for value in values]))


data = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [1_284_000, 936_000, 1_512_000, 1_067_000],
        "Margin": [0.128, -0.064, 0.173, 0.091],
    }
)

(
    tt(data, caption="Labels formatted with Mizani")
    .fmt(j="Revenue", fn=format_currency)
    .fmt(j="Margin", fn=format_percent)
    .fmt(j=["Revenue", "Margin"], escape=True)
    .style(j=["Revenue", "Margin"], align="r")
    .save("build/10_mizani.typ")
)
