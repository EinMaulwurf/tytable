"""
Typst-compilation validation — compiles rendered tables with the `typst` CLI.

Optional (per tytable_python_guide/13_testing.md §6): if the `typst` binary is
on PATH, compile each snapshot-worthy table and assert exit 0. Skipped locally
when typst is absent so it never blocks dev.
"""

import shutil
import subprocess

import polars as pl
import pytest

from tytable import tt

pytestmark = pytest.mark.typst

HAS_TYPST = shutil.which("typst") is not None


def _compile(typ_string: str, tmp_path) -> int:
    typ_file = tmp_path / "table.typ"
    out_file = tmp_path / "table.pdf"
    typ_file.write_text(typ_string, encoding="utf-8")
    return subprocess.run(
        ["typst", "compile", str(typ_file), str(out_file)],
        capture_output=True,
    ).returncode


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_basic(tmp_path):
    df = pl.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    assert _compile(tt(df).render("typst"), tmp_path) == 0


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
    assert _compile(typ, tmp_path) == 0


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_grouped(tmp_path):
    df = pl.DataFrame({"Q1_a": [1, 2], "Q1_b": [3, 4], "Q2_c": [5, 6], "Q2_d": [7, 8]})
    typ = tt(df).group(j="_").group(i={"Section": 1}).render("typst")
    assert _compile(typ, tmp_path) == 0


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_special_chars(tmp_path):
    df = pl.DataFrame({"A": ["$100", "#tag", "[bracket]"], "B": ["<x>", "*y*", "100%"]})
    assert _compile(tt(df).render("typst"), tmp_path) == 0


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_themes(tmp_path):
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
    for theme in ("default", "striped", "grid", "empty", "rotate"):
        assert _compile(tt(df, theme=theme).render("typst"), tmp_path) == 0
