"""Inline-style sharing must preserve native cells, scope, and compiled output."""

import shutil
import subprocess
from dataclasses import replace

import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._render_typst import TypstRenderer
from tytable._resolve import build

pytestmark = pytest.mark.typst


def _table(**kwargs):
    return tt(pl.DataFrame({"A": list(range(8)), "B": list(range(8, 16))}), **kwargs)


def test_long_repeated_styles_share_wrappers_across_native_cell_properties():
    table = _table().style(bold=True, italic=True, color="red")
    table.style(i=0, j="A", background="yellow", align="l", padding=0.5)
    output = table.render()

    assert output.count("#let tytable-style-1(body)") == 1
    assert output.count("#tytable-style-1[") == 16
    assert (
        'table.cell(align: left, fill: rgb("#ffff00"), inset: 0.5em)[#tytable-style-1[0]]' in output
    )
    assert_snapshot("shared_inline_styles", output)


@pytest.mark.parametrize("props", [{}, {"bold": True}, {"italic": True}])
def test_short_wrappers_stay_inline(props):
    assert "#let tytable-style-" not in _table().style(**props).render()


def test_sparse_long_styles_stay_inline():
    output = _table().style(i=[0, 1], j="A", bold=True, italic=True, color="red").render()
    assert "#let tytable-style-" not in output
    assert output.count('#strong[#emph[#text(fill: rgb("#ff0000"))') == 2


def test_helper_names_avoid_raw_content_and_remain_deterministic():
    raw = "#tytable-style-1"
    table = tt(pl.DataFrame({"A": [raw] * 8}), escape=False).style(
        bold=True, italic=True, color="red"
    )
    output = table.render()
    assert "#let tytable-style-1(" not in output
    assert "#let tytable-style-2(body)" in output
    assert output.count(f"#tytable-style-2[{raw}]") == 8
    assert output == table.render()


@pytest.mark.parametrize(
    "location",
    ["header", "group", "note", "marker", "width", "column-gutter", "row-gutter", "stroke"],
)
def test_helper_names_avoid_identifiers_in_other_table_inputs(location):
    identifier = "tytable-style-1"
    table = _table(notes=[{"text": "note", "marker": "*"}]).style(
        bold=True, italic=True, color="red"
    )
    table.group(j={"Group": ["A", "B"]})
    built = build(table, "typst")
    if location == "header":
        built.colnames_display[0] = identifier
    elif location == "group":
        built.col_groups[0][0] = identifier
    elif location == "note":
        built.notes[0] = replace(built.notes[0], text=identifier)
    elif location == "marker":
        built.notes[0] = replace(built.notes[0], marker=identifier)
    elif location == "width":
        built.column_widths = (identifier, "auto")
    elif location == "column-gutter":
        built.typst_options.column_gutter = identifier
    elif location == "row-gutter":
        built.typst_options.row_gutter = identifier
    else:
        built.typst_options.grid_stroke = identifier

    output = TypstRenderer(built.typst_options).render(built)
    assert "#let tytable-style-1(" not in output
    assert "#let tytable-style-2(body)" in output


def test_helpers_are_reset_when_renderer_is_reused():
    styled = _table().style(bold=True, italic=True, color="red")
    built = build(styled, "typst")
    renderer = TypstRenderer(built.typst_options)
    assert "#let tytable-style-" in renderer.render(built)
    plain = build(_table(), "typst")
    assert "tytable-style-" not in renderer.render(plain)


def test_different_wrappers_get_separate_helpers():
    output = _table().style(bold=True, italic=True, color="red").style(j="B", color="blue").render()
    assert output.count("#let tytable-style-") == 2
    assert output.count("#tytable-style-1[") == 8
    assert output.count("#tytable-style-2[") == 8


def test_covered_cells_do_not_justify_a_helper():
    table = tt(pl.DataFrame({"A": list(range(8))})).style(bold=True, italic=True, color="red")
    built = build(table, "typst")
    built.style_grid[(built.layout.header_rows, 0)]["rowspan"] = 8
    output = TypstRenderer(built.typst_options).render(built)
    assert "rowspan: 8" in output
    assert "#let tytable-style-" not in output


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not installed")
@pytest.mark.parametrize("figure", [False, True])
@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"fontsize": 1.4, "indent": 0.5},
        {"fontsize": 1.4, "indent": 0.5, "padding": (0.1, 0.2, 0.3, 0.4)},
        {"rotate": 15, "align": "r", "alignv": "b"},
        {"underline": True, "strikeout": True, "smallcaps": True},
        {"monospace": True},
    ],
)
def test_shared_styles_preserve_compiled_appearance(tmp_path, figure, extra):
    raw = "```text\nfirst line\n  indented line\n```\n#context text(size: text.size)[context]"
    raw += " #tytable-style-1"
    table = tt(
        pl.DataFrame({"A": [raw] * 8, "B": [1] * 8}),
        figure=figure,
        escape=False,
        notes=[{"i": 0, "j": "A", "text": "A targeted note", "marker": "*"}],
    )
    table.theme_plain().style(bold=True, italic=True, color="red", **extra)
    table.style(i=0, j="A", background="yellow")
    table.style(i=1, j="B", bold=False, color="blue")
    table.group(j={"Group": ["A", "B"]}).group(i={"Section": 4})
    table.style(i="header", bold=True, italic=True, color="red")
    if figure:
        table.rotate(5).resize(width=0.9, direction="down")
    actual = table.render()
    assert "#let tytable-style-2(body)" in actual
    assert raw in actual

    # Compare against the existing inline emission path without parsing raw
    # markup or normalizing wrapper order and native cell properties.
    built = build(table, "typst")
    renderer = TypstRenderer(built.typst_options)
    renderer._prepare_style_helpers = lambda lines, resolved: None
    reference = renderer.render(built)
    assert "#let tytable-style-" not in reference

    preamble = (
        "#set page(width: 30cm, height: auto, margin: 10pt)\n"
        "#set text(size: 9pt)\n#set table(inset: (x: 0.8em, y: 0.4em))\n"
        "#show strong: it => text(tracking: 0.1pt, it)\n"
        "#let tytable-style-1 = [outer scope]\n"
    )
    for name, source in (("reference", reference), ("actual", actual)):
        result = subprocess.run(
            ["typst", "compile", "-", str(tmp_path / f"{name}.png")],
            input=preamble + source + "\n#tytable-style-1",
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
    assert (tmp_path / "actual.png").read_bytes() == (tmp_path / "reference.png").read_bytes()
