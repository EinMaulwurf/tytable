"""
Example sparkline for tytable .plot() — copy/adapt for your own use.

Drop this function into your script and pass it to .plot(fun=sparkline).
A tight, low-padding figure keeps the line crisp when the image is scaled
down to cell height; pick a dark, saturated colour so it reads on any row
background (e.g. a striped theme).
"""

import matplotlib.pyplot as plt


def sparkline(values, *, color="#2c3e50", xlim=None, **kw):
    """
    Pure sparkline builder. Returns a matplotlib Figure; no file I/O.

    The *values* list is the per-cell data from the polars List column.
    """
    fig, ax = plt.subplots(figsize=(2.4, 0.8), dpi=150)
    ax.plot(range(len(values)), values, color=color, lw=3, solid_joinstyle="round")
    ax.set_axis_off()
    ax.margins(y=0.15)
    fig.tight_layout(pad=0)
    return fig
