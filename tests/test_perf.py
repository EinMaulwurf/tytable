"""
Performance gate — asserts a heavily-styled 120x30 table renders under budget.

The package's design avoids three common hotspots: per-style-entry full-grid
scans, marker insertion that repeatedly splits rendered output, and
row-binding in a loop with quadratic growth. This test guards against those
regressions.

Marked `typst` so it slices with the suite; not slow-skippable by default, but
the gate is generous (0.3 s) to absorb CI noise.
"""

import time

import polars as pl
import pytest

from tytable import tt

N_ROWS = 120
N_COLS = 30


def _build_heavy_table() -> "pl.DataFrame":
    return pl.DataFrame({f"c{i}": [float(r * i) for r in range(N_ROWS)] for i in range(N_COLS)})


@pytest.mark.typst
def test_heavy_table_under_budget():
    df = _build_heavy_table()
    tab = tt(df)
    heat = ["#fff", "#eee", "#ddd", "#ccc", "#bbb"]
    for r in range(N_ROWS):
        tab.style(i=r, background=heat[r % 5])
    tab.style(i="header", bold=True, line="b", line_width=0.08)

    t0 = time.perf_counter()
    out = tab.render("typst")
    dt = time.perf_counter() - t0

    assert out.startswith("#")
    assert len(out) > 0
    # Typical local target is < 100 ms; gate at 0.3 s for CI noise tolerance.
    assert dt < 0.3, f"render of {N_ROWS}x{N_COLS} table took {dt:.3f}s (budget 0.3s)"
