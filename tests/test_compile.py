"""
Typst-compilation validation — compiles rendered tables with the `typst` CLI.

When the optional `typst` binary is on PATH, compile each snapshot-worthy
table and assert exit 0. Skip locally when Typst is absent so the core Python
test suite does not require a system typesetter.
"""

import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from tytable import tt
from tytable.formatters import number, scientific

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
        .fmt(j="A", fn=number(digits=2))
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
@pytest.mark.parametrize("document_inset", ["5pt", "12pt", "(x: 0.8em, y: 0.4em)"])
@pytest.mark.parametrize(
    ("props", "wrapper", "inset"),
    [
        ({"bold": True, "italic": True}, "strong(emph(it))", "5pt"),
        ({"color": "red"}, 'text(fill: rgb("#ff0000"), it)', "5pt"),
        ({"fontsize": 1.5, "padding": 0.5}, "text(size: 1.5em, it)", "0.5em"),
        ({"indent": 0.5}, "pad(left: 0.5em, it)", "5pt"),
        (
            {"fontsize": 1.5, "indent": 0.5, "padding": (0.1, 0.2, 0.3, 0.4)},
            "pad(left: 0.5em, text(size: 1.5em, it))",
            "(top: 0.1em, right: 0.2em, bottom: 0.3em, left: 0.4em)",
        ),
        (
            {"rotate": 30, "fontsize": 1.5, "indent": 0.5, "padding": (0.1, 0.2, 0.3, 0.4)},
            "align(left, rotate(30deg, reflow: true, pad(left: 0.5em, text(size: 1.5em, it))))",
            "(top: 0.1em, right: 0.2em, bottom: 0.3em, left: 0.4em)",
        ),
        (
            {"underline": True, "strikeout": True, "smallcaps": True},
            "smallcaps(strike(underline(it)))",
            "5pt",
        ),
        ({"monospace": True}, "math.mono(it)", "5pt"),
    ],
)
def test_cell_styles_preserve_compiled_appearance(tmp_path, props, wrapper, inset, document_inset):
    # Independent reference: apply text/decorations around the resolved cell.
    # This catches changes to em-based padding, indentation, and rotation that
    # source snapshots and compilation-success checks cannot detect.
    inset_option = (
        f"inset: (x, y) => if x == 0 and y == 1 {{ {inset} }} else {{ 5pt }},"
        if "padding" in props
        else ""
    )
    reference = f"""#block(breakable: false)[
      #show table.cell.where(x: 0, y: 1): it => {wrapper}
      #table(
        columns: (auto, auto), stroke: none, rows: auto,
        align: (left, right),
        {inset_option}
        fill: (x, y) => if x == 0 and y == 1 {{ rgb("#dddddd") }},
        table.header(repeat: true, [A], [B]),
        [Alpha], [123], [Beta], [4],
      )
    ]"""
    actual = (
        tt(pl.DataFrame({"A": ["Alpha", "Beta"], "B": [123, 4]}), figure=False)
        .theme_plain()
        .style(i=0, j="A", background="#ddd", **props)
        .render("typst")
    )
    preamble = (
        f"#set page(width: 15cm, height: auto, margin: 10pt)\n#set table(inset: {document_inset})\n"
    )
    for name, source in (("reference", reference), ("actual", actual)):
        result = subprocess.run(
            ["typst", "compile", "-", str(tmp_path / f"{name}.png")],
            input=preamble + source,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
    assert (tmp_path / "actual.png").read_bytes() == (tmp_path / "reference.png").read_bytes()


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
@pytest.mark.parametrize("outer_alignment", ["left", "center", "right"])
def test_vertical_only_alignment_inherits_document_alignment(tmp_path, outer_alignment):
    actual = (
        tt(
            pl.DataFrame({"A": [1], "B": [222]}),
            figure=False,
            column_widths=["3cm", "3cm"],
        )
        .theme_plain()
        .style(i=0, j="A", alignv="m")
        .render("typst")
    )
    reference = """#block(breakable: false)[
      #table(
        columns: (3cm, 3cm), stroke: none,
        align: (x, y) => if x == 0 and y == 1 { horizon } else { right },
        table.header([A], [B]), [1], [222],
      )
    ]"""
    for name, source in (("actual", actual), ("reference", reference)):
        result = subprocess.run(
            ["typst", "compile", "-", str(tmp_path / f"{name}.png")],
            input=(
                "#set page(width: 15cm, height: auto, margin: 10pt)\n"
                f"#align({outer_alignment})[\n{source}\n]"
            ),
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
    assert (tmp_path / "actual.png").read_bytes() == (tmp_path / "reference.png").read_bytes()


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_coalesced_font_style_excludes_footer(tmp_path):
    actual = (
        tt(pl.DataFrame({"A": [1, 2]}), figure=False, notes=["Note"])
        .theme_plain()
        .style(i=["header", "data"], fontsize=1.5)
        .render("typst")
    )
    reference = """#block(breakable: false)[
      #show table.cell: it => if it.y < 3 { text(size: 1.5em, it) } else { it }
      #table(
        columns: 1, stroke: none, align: right,
        table.header([A]), [1], [2],
        table.footer(repeat: false, table.cell(align: left, colspan: 1, [Note])),
      )
    ]"""
    for name, source in (("actual", actual), ("reference", reference)):
        result = subprocess.run(
            ["typst", "compile", "-", str(tmp_path / f"{name}.png")],
            input="#set page(width: 15cm, height: auto, margin: 10pt)\n" + source,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
    assert (tmp_path / "actual.png").read_bytes() == (tmp_path / "reference.png").read_bytes()


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
def test_compile_scientific_formatter(tmp_path):
    df = pl.DataFrame({"value": [1230000.0, -0.000123, 0.0, None, float("inf")]})
    typ = tt(df).fmt(fn=scientific(locale="de_DE")).render("typst")
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
@pytest.mark.parametrize("figure", [True, False])
@pytest.mark.parametrize("width", [0.8, "8cm"])
def test_compile_table_and_column_widths(tmp_path, figure, width):
    df = pl.DataFrame({"A": [1.5, 2.5], "B": [3.5, 4.5]})
    typ = tt(
        df,
        figure=figure,
        width=width,
        column_widths=["3cm", "3cm"],
    ).render("typst")
    _compile(typ, tmp_path)


@pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not installed")
@pytest.mark.parametrize(
    ("width", "expected_points"), [(1, 12 * 72 / 2.54), ("8cm", 8 * 72 / 2.54)]
)
def test_compiled_table_width_matches_requested_width(tmp_path, width, expected_points):
    df = pl.DataFrame({"A": ["x"], "B": ["y"]})
    typ = tt(df, figure=False, width=width).render("typst")
    source = "#set page(width: 12cm, height: auto, margin: 0pt)\n" + typ
    output = tmp_path / "table.svg"

    result = subprocess.run(
        ["typst", "compile", "-", str(output), "--format", "svg"],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rule_lengths = [
        float(length)
        # Typst versions use either a horizontal command or an absolute line,
        # and differ in whether they include trailing whitespace in path data.
        for length in re.findall(
            r'<path[^>]* d="M 0 0\s*(?:h|L)\s+([0-9.]+)(?:\s+0)?\s*"',
            output.read_text(),
        )
    ]
    assert rule_lengths
    assert max(rule_lengths) == pytest.approx(expected_points, abs=1)


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
