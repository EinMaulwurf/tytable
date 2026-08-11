"""
Typst-compilation validation — compiles rendered tables with the `typst` CLI.

When the optional `typst` binary is on PATH, compile each snapshot-worthy
table and assert exit 0. Skip locally when Typst is absent so the core Python
test suite does not require a system typesetter.
"""

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from tytable import tt

pytestmark = pytest.mark.typst

HAS_TYPST = shutil.which("typst") is not None


def test_compile_rejects_unknown_binary_suffix(tmp_path):
    with pytest.raises(ValueError, match=r"\.pdf, \.png, or \.svg"):
        tt(pl.DataFrame({"A": [1]})).compile(tmp_path / "table.typ")


def test_compile_validates_png_resolution(tmp_path):
    table = tt(pl.DataFrame({"A": [1]}))
    with pytest.raises(ValueError, match="only for PNG"):
        table.compile(tmp_path / "table.pdf", ppi=144)
    with pytest.raises(ValueError, match="positive"):
        table.compile(tmp_path / "table.png", ppi=0)


def test_compile_reports_missing_typst_executable(tmp_path):
    with pytest.raises(RuntimeError, match="was not found"):
        tt(pl.DataFrame({"A": [1]})).compile(
            tmp_path / "table.pdf", executable="definitely-not-a-typst-executable"
        )


def test_compile_forwards_cli_options_without_intermediate_file(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    output = tmp_path / "nested" / "table-{p}.png"

    tt(pl.DataFrame({"A": [1]})).compile(
        output,
        root=tmp_path,
        font_paths=fonts,
        pages="1-2",
        ppi=200,
    )

    command, kwargs = calls[0]
    assert command == [
        "typst",
        "compile",
        "--root",
        str(tmp_path),
        "--font-path",
        str(fonts),
        "--pages",
        "1-2",
        "--ppi",
        "200",
        "-",
        str(output),
    ]
    assert kwargs["input"].startswith("#")
    assert kwargs["cwd"] == tmp_path
    assert not list(tmp_path.rglob("*.typ"))


def test_compile_includes_typst_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="error: bad table"),
    )
    with pytest.raises(RuntimeError, match="error: bad table"):
        tt(pl.DataFrame({"A": [1]})).compile(tmp_path / "table.pdf")


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
@pytest.mark.parametrize("suffix", ["pdf", "png", "svg"])
def test_public_compile_writes_binary_output(tmp_path, suffix):
    output = tmp_path / f"table.{suffix}"
    result = tt(pl.DataFrame({"A": [1, 2]})).compile(output)

    assert result is None
    assert output.exists()
    assert output.stat().st_size > 0


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_public_compile_resolves_referenced_image_from_root(tmp_path):
    (tmp_path / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<rect width="10" height="10" fill="red"/></svg>',
        encoding="utf-8",
    )
    output = tmp_path / "table.pdf"

    (
        tt(pl.DataFrame({"Logo": [1]}))
        .images(j="Logo", paths=["logo.svg"])
        .compile(output, root=tmp_path, static_images="reference")
    )

    assert output.exists()


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
        tt(df, caption="Styled", column_gutter="0.25em", row_gutter=1)
        .fmt(j="A", digits=2)
        .style(i="header", bold=True, color="white", background="#333")
        .style(
            i=0,
            j="A",
            align="c",
            line="tblr",
            line_style="dash-dotted",
            padding=(0.25, 0.5),
        )
        .style(i="header", line="b", line_style="none")
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
        tt(df).theme_plain(),
        tt(df).rotate(),
        tt(df).multipage(),
        tt(df).multipage(repeat_headers=False),
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


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_embedded_static_svg(tmp_path):
    image = tmp_path / "logo.svg"
    image.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<rect width="10" height="10" fill="red"/></svg>',
        encoding="utf-8",
    )
    typ = (
        tt(pl.DataFrame({"Logo": [1]}))
        .images(j="Logo", paths=[str(image)])
        .render("typst", static_images="embed")
    )
    _compile(typ, tmp_path)
