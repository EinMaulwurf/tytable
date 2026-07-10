"""Images & sparklines example — embedding generated plots in cells.

Requires the `images` extra:  pip install tytable[images]
"""

import matplotlib.pyplot as plt
import polars as pl

from tytable import tt


def sparkline(values, *, color="#2c3e50", **kw):
    fig, ax = plt.subplots(figsize=(2.4, 0.8), dpi=150)
    ax.plot(range(len(values)), values, color=color, lw=3, solid_joinstyle="round")
    ax.set_axis_off()
    ax.margins(y=0.15)
    fig.tight_layout(pad=0)
    return fig


df = pl.DataFrame(
    {
        "Product": ["A", "B", "C", "D"],
        "Score": [85.43, 72.10, 91.87, 68.55],
        "Trend": [[1, 3, 2, 5, 4], [5, 4, 3, 2, 1], [1, 2, 3, 4, 5], [3, 1, 4, 1, 5]],
    }
)

(
    tt(df, caption="Product scores with trend sparklines", theme="striped")
    .fmt(j="Score", digits=2)
    .plot(j="Trend", fun=sparkline, height=1.5, color="#2c3e50")
    .style(j="Score", align="c")
    .style(i="header", bold=True, line="b", line_width=0.08)
    .style(i=0, bold=True, background="#2c3e50", color="white")
    .group(i={"Highlight": 2})
    .style(i="groupi", bold=True, background="#ecf0f1")
    .save("build/07_images.typ", assets="assets")
)
