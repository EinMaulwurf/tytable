"""Polars-first formatting — currency, thousands separators, and nulls handled before tt()."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [12450.5, 9800.0, 15200.25, None],
        "Status": ["active", "active", None, "paused"],
    }
)

# Round, format as USD currency with thousands separators, and fill nulls —
# all in polars, so tt() only ever sees strings.
df = df.with_columns(
    pl.col("Revenue")
    .round(2)
    .map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.Utf8)
    .fill_null("—"),
    pl.col("Status").fill_null("n/a"),
)

(
    tt(df, caption="Regional revenue (formatted in polars)")
    # Revenue is now a string column, so restore numeric-style alignment explicitly.
    .style(j="Revenue", align="r")
    .save("build/11_format_polars.typ")
)
