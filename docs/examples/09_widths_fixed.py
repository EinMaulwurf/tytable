"""Column-width example — a fixed first column with the rest auto-sized."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Model": ["A-100", "B-200", "C-300", "D-400"],
        "Accuracy": [0.923, 0.941, 0.918, 0.955],
        "Latency (ms)": [12.4, 9.8, 15.1, 11.0],
        "Notes": ["baseline", "best accuracy", "fastest", "recommended"],
    }
)

(
    tt(df, caption="Fixed first column, rest auto", width=["3.5cm", None, None, None])
    .fmt(j="Accuracy", digits=3)
    .fmt(j="Latency (ms)", digits=1)
    .style(i="header", bold=True)
    .save("build/09_widths_fixed.typ")
)
