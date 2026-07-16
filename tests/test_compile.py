"""
Typst-compilation validation — compiles rendered tables with the `typst` CLI.

Optional (per tytable_python_guide/13_testing.md §6): if the `typst` binary is
on PATH, compile each snapshot-worthy table and assert exit 0. Skipped locally
when typst is absent so it never blocks dev.
"""

import shutil
import subprocess
from pathlib import Path

import polars as pl
import pytest

from tytable import tt

pytestmark = pytest.mark.typst

HAS_TYPST = shutil.which("typst") is not None


def _compile(typ_string: str, tmp_path: Path) -> None:
    typ_file = tmp_path / "table.typ"
    out_file = tmp_path / "table.pdf"
    typ_file.write_text(typ_string, encoding="utf-8")
    result = subprocess.run(
        ["typst", "compile", str(typ_file), str(out_file)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            "Typst compilation failed"
            f"\n\nstdout:\n{result.stdout or '(empty)'}"
            f"\n\nstderr:\n{result.stderr or '(empty)'}",
            pytrace=False,
        )


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_basic(tmp_path):
    df = pl.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    _compile(tt(df).render("typst"), tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_without_figure(tmp_path):
    df = pl.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    typ = tt(df, figure=False).style(i=0, j="A", bold=True).render("typst")
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_labelled_figure(tmp_path):
    df = pl.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    typ = tt(df, label="results-table").render("typst") + "\nSee @results-table."
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_styled(tmp_path):
    df = pl.DataFrame({"A": [1.5, 2.5], "B": [3.5, 4.5]})
    typ = (
        tt(df, caption="Styled")
        .fmt(j="A", digits=2)
        .style(i="header", bold=True, color="white", background="#333")
        .style(i=0, j="A", align="c", line="tblr")
        .render("typst")
    )
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_grouped(tmp_path):
    df = pl.DataFrame({"Q1_a": [1, 2], "Q1_b": [3, 4], "Q2_c": [5, 6], "Q2_d": [7, 8]})
    typ = tt(df).group(delimiter="_").group(i={"Section": 1}).render("typst")
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_special_chars(tmp_path):
    df = pl.DataFrame({"A": ["$100", "#tag", "[bracket]"], "B": ["<x>", "*y*", "100%"]})
    _compile(tt(df).render("typst"), tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_math_and_linebreak(tmp_path):
    df = pl.DataFrame({"Formula": ["x^2 + y^2"], "Detail": ["first|second"]})
    typ = tt(df).fmt(j="Formula", math=True).fmt(j="Detail", linebreak="|").render("typst")
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_themes(tmp_path):
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
    tables = (
        tt(df),
        tt(df).theme_striped(),
        tt(df).theme_grid(),
        tt(df).theme_empty(),
        tt(df).theme_rotate(),
        tt(df).theme_multipage(),
        tt(df).theme_multipage(repeat_headers=False),
    )
    for table in tables:
        _compile(table.render("typst"), tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_alpha_hex(tmp_path):
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
    typ = (
        tt(df)
        .style(i="header", background="#3337")  # 4-digit hex alpha
        .style(i=0, j="A", background="#ff000080")  # 8-digit hex alpha
        .style(i=1, j="B", color="#00ff0033")  # 8-digit hex alpha
        .render("typst")
    )
    _compile(typ, tmp_path)
