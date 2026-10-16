"""Scientific measurements with native superscripts and a plain-text fallback."""

import polars as pl

from tytable import tt
from tytable.formatters import scientific

df = pl.DataFrame(
    {
        "Sample": ["Large", "Small", "Negative", "Zero", "Missing"],
        "Measurement": [1230000.0, 0.000123, -45600.0, 0.0, None],
    }
)

(
    tt(df, caption="Scientific measurements")
    .fmt(j="Measurement", fn=scientific(digits=2))
    .save("build/02_scientific.typ")
)
