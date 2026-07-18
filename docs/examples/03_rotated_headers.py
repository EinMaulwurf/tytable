"""Rotated headers — keep long labels over compact numeric columns."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Model": ["Baseline", "Compact", "Ensemble"],
        "Accuracy": [0.81, 0.84, 0.87],
        "Precision": [0.78, 0.83, 0.86],
        "Recall": [0.85, 0.82, 0.88],
        "F1 score": [0.81, 0.82, 0.87],
        "Parameters (M)": [2.4, 1.1, 7.3],
    }
)

compact_columns = ["Accuracy", "Precision", "Recall", "F1 score", "Parameters (M)"]

(
    tt(
        df,
        caption="Rotated labels keep numeric columns compact",
        width=["3cm", "1.25cm", "1.25cm", "1.25cm", "1.25cm", "1.25cm"],
    )
    .fmt(j=compact_columns, digits=2)
    .style(i="header", bold=True, align="l", alignv="b", line="b")
    .style(i="header", j=compact_columns, rotate=-55)
    .style(i="data", j=compact_columns, align="c")
    .save("build/03_rotated_headers.typ")
)
