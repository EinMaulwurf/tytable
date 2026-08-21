"""
Performance gates for representative styled, HTML, and replacement-heavy tables.

The package's design avoids per-style-entry full-grid scans, marker insertion
that repeatedly splits rendered output, row-binding in a loop with quadratic
growth, and repeated preparation of render-wide values inside cell loops.
These tests guard both wall-clock performance and those algorithmic invariants.

Backend markers keep the gates sliceable with the suite. Wall-clock budgets
retain CI headroom, while call-count assertions guard the exact loop invariants.
"""

import time

import polars as pl
import pytest

from tytable import tt
from tytable._indices import RowLayout
from tytable._render_ascii import AsciiRenderer
from tytable._render_html import HtmlRenderer
from tytable._resolve import build

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
    # Typical local target is < 100 ms; retain headroom for slower CI runners.
    assert dt < 0.3, f"render of {N_ROWS}x{N_COLS} table took {dt:.3f}s (budget 0.3s)"


@pytest.mark.html
def test_plain_html_table_under_budget():
    df = pl.DataFrame({f"c{i}": list(range(1000)) for i in range(30)})
    tab = tt(df).theme_plain()

    t0 = time.perf_counter()
    out = tab.render("html")
    dt = time.perf_counter() - t0

    assert out.startswith("<table")
    # Branch-coverage instrumentation magnifies HTML's many small Python calls.
    assert dt < 0.9, f"HTML render of 1000x30 table took {dt:.3f}s (budget 0.9s)"


class _CountingDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_calls = 0

    def items(self):
        self.items_calls += 1
        return super().items()


@pytest.mark.typst
def test_replacement_mapping_is_prepared_once():
    replacement = _CountingDict({value: f"value-{value}" for value in range(100)})
    df = pl.DataFrame({"value": list(range(1000))})

    out = tt(df).fmt(replace=replacement).render("typst")

    assert "value\\-99" in out
    assert replacement.items_calls == 1


@pytest.mark.parametrize("renderer", [HtmlRenderer(), AsciiRenderer()])
def test_renderers_resolve_group_rows_once(monkeypatch, renderer):
    table = tt(pl.DataFrame({"a": list(range(100)), "b": list(range(100))})).group(i={"Group": 50})
    built = build(table, "html" if isinstance(renderer, HtmlRenderer) else "ascii")
    original = RowLayout.groupi_rows.fget
    calls = 0

    def counted_groupi_rows(layout):
        nonlocal calls
        calls += 1
        return original(layout)

    monkeypatch.setattr(RowLayout, "groupi_rows", property(counted_groupi_rows))
    renderer.render(built)

    assert calls == 1
