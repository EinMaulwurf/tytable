"""Full report example — formatting, styling, grouping, theme, and sparklines.

Combines every feature into a single realistic table. Requires the `images`
extra (`pip install tinytables[images]`).

Run:  uv run python examples/full_report.py
"""

import polars as pl

from tinytables import tt


def sparkline(values, *, color="black", xlim=None, **kw):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 2), dpi=100)
    ax.plot(range(len(values)), values, color=color, lw=2)
    ax.set_axis_off()
    return fig


df = pl.DataFrame(
    {
        "Product": ["A", "B", "C", "D"],
        "Score": [85.43, 72.10, 91.87, 68.55],
        "Trend": [[1, 3, 2, 5, 4], [5, 4, 3, 2, 1], [1, 2, 3, 4, 5], [3, 1, 4, 1, 5]],
    }
)

tab = (
    tt(df, caption="Product scores with trend sparklines", theme="striped")
    .fmt(j="Score", digits=2)
    .plot(j="Trend", fun=sparkline, height=1.5, color="#4CAF50")
    .style(j="Score", align="c")
    .style(i="header", bold=True, line="b", line_width=0.08)
    .style(i=0, bold=True, background="#2c3e50", color="white")
    .group(i={"Highlight": 2})
    .style(i="groupi", bold=True, background="#ecf0f1")
)

print("--- Typst output ---")
print(tab.render("typst"))

print("\n--- HTML preview ---")
print(tab.render("html"))

tab.save("report_assets/products.typ")
print("\nSaved to report_assets/products.typ")
