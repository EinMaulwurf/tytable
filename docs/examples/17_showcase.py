"""Showcase — a publication-ready model comparison table."""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Model": ["Linear", "Forest", "Boosted", "Neural"],
        "Accuracy": [0.842, 0.913, 0.927, 0.919],
        "F1": [0.816, 0.901, 0.921, 0.914],
        "Latency": [1.2, 8.7, 4.1, 12.6],
        "Parameters": [24, 18_400, 7_800, 52_100],
    }
)

(
    tt(
        df,
        caption="Model selection scorecard",
        label="model-scorecard",
        notes=[
            {"text": "Highest validation accuracy.", "i": 2, "j": "Accuracy"},
            "Latency measured on the same CPU batch (milliseconds; lower is better).",
        ],
        width=["2.8cm", "1fr", "1fr", "1fr", "1.2fr"],
    )
    .theme_plain()
    .group(j={"Quality": ["Accuracy", "F1"], "Cost": ["Latency", "Parameters"]})
    .fmt(j=["Accuracy", "F1"], digits=3)
    .fmt(j="Latency", digits=1)
    .style(i="groupj", bold=True, color="#153243", background="#dbeff0")
    .style(i="header", bold=True, color="white", background="#153243")
    .style(j="Model", bold=True)
    .style(i=[1, 3], background="#f4f7f8")
    .style(i=2, bold=True, background="#d7f0ea", line="tb", line_color="#087e8b")
    .style(i=2, j="Accuracy", color="#087e8b")
    .style(i="caption", bold=True, color="#153243", fontsize=1.2)
    .style(i="notes", italic=True, color="#52606d")
    .save("build/17_showcase.typ")
)
