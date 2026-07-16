import polars as pl
import pytest

import tytable
from tests.helpers import assert_snapshot
from tytable import TyTable, tt
from tytable._escape import escape_typst
from tytable._resolve import build

EXPECTED_BASIC_TYP = (
    '#show figure.where(kind: "tytable"): set block(breakable: false)\n'
    "#figure(\n"
    '  kind: "tytable",\n'
    '  supplement: "Table",\n'
    "\n"
    "block[\n"
    "  #let style-dict = (\n"
    "  )\n"
    "\n"
    "  #let style-array = (\n"
    "  )\n"
    "\n"
    "  #let get-style(x, y) = {\n"
    '    let key = str(y) + "_" + str(x)\n'
    "    if key in style-dict { style-array.at(style-dict.at(key)) } else { none }\n"
    "  }\n"
    "\n"
    "  #show table.cell: it => {\n"
    "    if style-array.len() == 0 { return it }\n"
    "    let style = get-style(it.x, it.y)\n"
    "    if style == none { return it }\n"
    "    let tmp = it\n"
    '    if ("fontsize" in style) { tmp = text(size: style.fontsize, tmp) }\n'
    '    if ("color" in style) { tmp = text(fill: style.color, tmp) }\n'
    '    if ("indent" in style) { tmp = pad(left: style.indent, tmp) }\n'
    '    if ("underline" in style) { tmp = underline(tmp) }\n'
    '    if ("italic" in style) { tmp = emph(tmp) }\n'
    '    if ("bold" in style) { tmp = strong(tmp) }\n'
    '    if ("mono" in style) { tmp = math.mono(tmp) }\n'
    '    if ("strikeout" in style) { tmp = strike(tmp) }\n'
    '    if ("smallcaps" in style) { tmp = smallcaps(tmp) }\n'
    '    if ("rotate" in style) {\n'
    '      let a = if "align" in style { style.align } else { left }\n'
    "      tmp = align(a, rotate(style.rotate, reflow: true, tmp))\n"
    "    }\n"
    "    tmp\n"
    "  }\n"
    "\n"
    "  #table(\n"
    "    columns: (auto, auto),\n"
    "    stroke: none,\n"
    "    rows: auto,\n"
    "    align: (x, y) => {\n"
    "      let style = get-style(x, y)\n"
    '      if style != none and "align" in style { style.align } else { left }\n'
    "    },\n"
    "    fill: (x, y) => {\n"
    "      let style = get-style(x, y)\n"
    '      if style != none and "background" in style { style.background }\n'
    "    },\n"
    "    table.header(\n"
    "      repeat: true,\n"
    "      [A],[B],\n"
    "    ),\n"
    "    [1],[2],\n"
    "    [3],[4],\n"
    "  )\n"
    "]\n"
    ")"
)


def test_public_table_class_is_tytable():
    table = tt(pl.DataFrame({"A": [1]})).theme_empty()

    assert isinstance(table, TyTable)
    assert "TyTable" in tytable.__all__
    assert "TinyTable" not in tytable.__all__
    assert not hasattr(tytable, "TinyTable")


@pytest.mark.typst
class TestByteExact:
    def test_byte_exact_acceptance(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        result = tt(df).theme_empty().render("typst")
        assert result == EXPECTED_BASIC_TYP

    def test_invariant(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df).theme_empty()
        assert t.render("typst") == t.render("typst")

    def test_render_does_not_mutate_resolution_state(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df)
        state = (len(t._style_directives), len(t._format_directives), t._nhead)

        first = t.render("typst")
        second = t.render("typst")

        assert first == second
        assert (len(t._style_directives), len(t._format_directives), t._nhead) == state
        assert t._n_merged_body_rows == 0

    def test_pristine_data(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df)
        _ = t.render("typst")
        assert t._data.equals(df)
        assert t._data is not df


@pytest.mark.typst
class TestSnapshots:
    def test_basic_2x2(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        assert_snapshot("basic_typ", tt(df).theme_empty().render("typst"))

    def test_basic_3x3(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        assert_snapshot("basic_3x3", tt(df).theme_empty().render("typst"))


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_empty_dataframe_renders_with_all_backends(output):
    df = pl.DataFrame(schema={"A": pl.Int64, "B": pl.String})
    rendered = tt(df).theme_empty().render(output)
    assert rendered
    assert "A" in rendered
    assert "B" in rendered


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_unicode_text_survives_all_renderers(output):
    values = ["日本語", "table 🎉", "مرحبا", "e\u0301"]
    rendered = tt(pl.DataFrame({"text": values})).theme_empty().render(output)
    for value in values:
        assert value in rendered


@pytest.mark.parametrize(("suffix", "output"), [(".typ", "typst"), (".html", "html")])
def test_save_plain_output(tmp_path, suffix, output):
    table = tt(pl.DataFrame({"A": [1], "B": [2]})).theme_empty()
    expected = table.render(output)
    destination = tmp_path / f"output{suffix}"
    table.save(str(destination))
    assert destination.read_text(encoding="utf-8") == expected


def test_build_rejects_unknown_output():
    table = tt(pl.DataFrame({"A": [1]})).theme_empty()
    with pytest.raises(NotImplementedError, match="output='markdown' not implemented"):
        build(table, "markdown")


@pytest.mark.typst
class TestCaption:
    def test_caption_present(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, caption="My Table").render("typst")
        assert "  caption: text([My Table])," in out
        assert out.index("  caption:") < out.index("  kind:")
        assert_snapshot("caption_present", out)

    def test_caption_absent(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df).theme_empty().render("typst")
        assert "caption:" not in out
        assert_snapshot("basic_typ", out)

    def test_label_attached_to_figure(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, label="results-table").theme_empty().render("typst")
        assert out.endswith(") <results-table>")

    def test_figure_false_emits_table_without_figure(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, figure=False).theme_empty().style(i=0, bold=True).render("typst")
        assert "#figure(" not in out
        assert "#table(" in out
        assert "#block(breakable: false)[" in out
        assert "bold: true" in out

    @pytest.mark.parametrize("metadata", [{"caption": "Results"}, {"label": "results"}])
    def test_figure_false_rejects_figure_metadata(self, metadata):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        with pytest.raises(ValueError, match="caption and label require figure=True"):
            tt(df, figure=False, **metadata)

    @pytest.mark.parametrize("label", ["has space", "<wrapped>", "bad#label", ""])
    def test_invalid_label_rejected(self, label):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        with pytest.raises(ValueError, match="label must contain"):
            tt(df, label=label)

    def test_theme_cannot_silently_drop_caption(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        table = tt(df, caption="Results").theme_empty()
        table._typst_opts.figure = False
        with pytest.raises(ValueError, match="caption and label require figure=True"):
            table.render("typst")


@pytest.mark.typst
class TestNoColnames:
    def test_no_colnames(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, colnames=False).render("typst")
        assert "table.header" not in out
        assert_snapshot("no_colnames", out)


@pytest.mark.typst
class TestEscape:
    def test_plain_text_unchanged(self):
        assert escape_typst("plain text") == "plain text"

    @pytest.mark.parametrize(("value", "expected"), [(42, "42"), (True, "True"), (None, "None")])
    def test_non_string_values_are_converted(self, value, expected):
        assert escape_typst(value) == expected

    def test_hash_escaped(self):
        assert escape_typst("#") == "\\#"

    def test_bracket_escaped(self):
        assert escape_typst("[") == "\\["

    def test_backtick_escaped(self):
        assert escape_typst("`") == "\\`"

    def test_tilde_escaped(self):
        assert escape_typst("~") == "\\~"

    def test_single_backslash(self):
        assert escape_typst("\\") == "\\\\"

    def test_backslash_hash_no_cascade(self):
        assert escape_typst("\\#") == "\\\\\\#"

    def test_no_double_escape(self):
        assert escape_typst("a\\b") == "a\\\\b"

    def test_cell_hash_escaped_in_output(self):
        df = pl.DataFrame({"A": ["x#y"]})
        out = tt(df).render("typst")
        assert "[x\\#y]," in out

    def test_cell_bracket_escaped_in_output(self):
        df = pl.DataFrame({"A": ["x[y"]})
        out = tt(df).render("typst")
        assert "\\[" in out


@pytest.mark.skipif(not __import__("shutil").which("typst"), reason="typst CLI not installed")
@pytest.mark.typst
class TestCompile:
    def test_compiles(self, tmp_path):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        f = tmp_path / "t.typ"
        f.write_text(tt(df).render("typst"))
        import subprocess

        res = subprocess.run(["typst", "compile", str(f), str(tmp_path / "o.pdf")])
        assert res.returncode == 0
