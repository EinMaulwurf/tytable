"""Semantic formatter example — German currency, percentage, number, and date output."""

from datetime import date

import polars as pl

from tytable import tt
from tytable.formatters import currency, number, percent
from tytable.formatters import date as date_formatter

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
        fn=currency("EUR", locale="de_DE", accounting=True),
    )
    .fmt(j="Margin", fn=percent(locale="de_DE", digits=1))
    .fmt(j="Orders", fn=number(locale="de_DE", digits=0))
    .fmt(j="Date", fn=date_formatter("%d.%m.%Y"))
    .save("build/02_semantic_formatters.typ")
)
