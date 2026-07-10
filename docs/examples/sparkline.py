"""Example sparkline for tytable .plot() — copy/adapt for your own use.

Drop this function into your script and pass it to .plot(fun=sparkline).
"""

import matplotlib.pyplot as plt


def sparkline(values, *, color="black", xlim=None, **kw):
    """Pure sparkline builder. Returns a matplotlib Figure; no file I/O.

    The *values* list is the per-cell data from the polars List column.
    """
    fig, ax = plt.subplots(figsize=(6, 2), dpi=100)
    ax.plot(range(len(values)), values, color=color, lw=2)
    ax.set_axis_off()
    return fig
