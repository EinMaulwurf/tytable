"""Semantic formatter example — German currency, percentage, number, and date output."""

from datetime import date

import polars as pl

from tytable import formatters, tt

df = pl.DataFrame(
    {
        "Product": ["Standard", "Return", "Enterprise", "Pending"],
        "Revenue": [1023.87, -1250.5, 2_500_000.0, None],
        "Margin": [0.1234, -0.034, 0.287, None],
        "Orders": [1240, 85, 18_420, None],
        "Date": [date(2026, 8, 11), date(2026, 8, 12), date(2026, 8, 13), None],
    }
)

(
    tt(df, caption="German report conventions", width=1)
    .fmt(
        j="Revenue",
        formatter=formatters.currency("EUR", locale="de_DE", accounting=True),
    )
    .fmt(j="Margin", formatter=formatters.percent(locale="de_DE", digits=1))
    .fmt(j="Orders", formatter=formatters.number(locale="de_DE", digits=0))
    .fmt(j="Date", formatter=formatters.date("%d.%m.%Y"))
    .save("build/02_semantic_formatters.typ")
)
