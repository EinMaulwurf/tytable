"""Custom formatting function — abbreviate large numbers (1028 -> "1.0 thousand")."""

import polars as pl

from tytable import tt


def humanize(values: list[str]) -> list[str]:
    """Abbreviate large numbers into a human-readable scale."""

    def scale(n: float) -> str:
        if abs(n) >= 1_000_000:
            return f"{n / 1_000_000:.1f} million"
        if abs(n) >= 1_000:
            return f"{n / 1_000:.1f} thousand"
        return str(int(n))

    return [scale(float(v)) for v in values]


df = pl.DataFrame(
    {
        "City": ["Geneva", "Zurich", "Lugano"],
        "Population": [201818, 415367, 2729179],
    }
)

(
    tt(df, caption="City populations, human-readable")
    .fmt(j="Population", fn=humanize)
    .style(j="Population", align="r")
    .save("build/10_format_fn.typ")
)
