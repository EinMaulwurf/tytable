"""Performance gate — asserts a heavily-styled 120x30 table renders under budget.

See tytable_python_guide/15_performance.md §4. The package's design avoids
tinytable R's three hotspots (per-style-entry full-grid scans, marker insertion
re-splitting the output string, rbind-in-loop O(n^2) growth). This test guards
against regressions.

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
    tab = tt(df, theme="default")
    heat = ["#fff", "#eee", "#ddd", "#ccc", "#bbb"]
    for r in range(N_ROWS):
        tab.style(i=r, background=heat[r % 5])
    tab.style(i="header", bold=True, line="b", line_width=0.08)

    t0 = time.perf_counter()
    out = tab.render("typst")
    dt = time.perf_counter() - t0

    assert out.startswith("#")
    assert len(out) > 0
    # Target < 100 ms (15 §4); gate at 0.3 s for CI noise tolerance.
    assert dt < 0.3, f"render of {N_ROWS}x{N_COLS} table took {dt:.3f}s (budget 0.3s)"
