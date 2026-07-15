"""
Images & sparklines example — embedding existing files and generated plots.

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
        "Flag": ["DE", "FR", "IT"],
        "Country": ["Germany", "France", "Italy"],
        "Score": [85.43, 72.10, 91.87],
        "Trend": [[1, 3, 2, 5, 4], [5, 4, 3, 2, 1], [1, 2, 3, 4, 5]],
    }
)

(
    tt(df, caption="Country scores with flags and trend sparklines")
    .theme_striped()
    .fmt(j="Score", digits=2)
    # Existing image paths are relative to the saved build/07_images.typ fragment.
    .images(
        j="Flag",
        paths=[
            "../assets/flags/de.svg",
            "../assets/flags/fr.svg",
            "../assets/flags/it.svg",
        ],
        height=1.2,
    )
    .plot(j="Trend", fun=sparkline, height=1.5, color="#2c3e50")
    .style(j="Score", align="c")
    .style(
        i="header",
        bold=True,
        background="#2c3e50",
        color="white",
        line="b",
        line_width=0.08,
    )
    .save("build/07_images.typ", assets="assets")
)
