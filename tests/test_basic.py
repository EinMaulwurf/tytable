import inspect

import polars as pl
import pytest

import tytable
from tests.helpers import assert_snapshot
from tytable import NoteDict, TyTable, tt
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
    '      if style != none and "align" in style { style.align } else { (right, right).at(x) }\n'
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
    table = tt(pl.DataFrame({"A": [1]})).theme_plain()

    assert isinstance(table, TyTable)
    assert "TyTable" in tytable.__all__
    assert "TinyTable" not in tytable.__all__
    assert not hasattr(tytable, "TinyTable")


def test_construction_api_excludes_removed_parameters():
    assert "rownames" not in inspect.signature(tt).parameters
    assert "digits" not in inspect.signature(tt).parameters
    assert "colnames_override" not in inspect.signature(tt).parameters
    assert "finalize" not in inspect.signature(tt).parameters
    assert "rownames" not in inspect.signature(TyTable).parameters
    assert "digits" not in inspect.signature(TyTable).parameters
    assert "colnames_override" not in inspect.signature(TyTable).parameters


def test_note_dict_is_public_and_describes_note_keys():
    note: NoteDict = {"text": "Source", "marker": "*", "i": 0, "j": "A"}

    assert "NoteDict" in tytable.__all__
    assert set(NoteDict.__annotations__) == {"text", "marker", "i", "j"}
    assert note["text"] == "Source"


@pytest.mark.typst
class TestByteExact:
    def test_byte_exact_acceptance(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        result = tt(df).theme_plain().render("typst")
        assert result == EXPECTED_BASIC_TYP

    def test_invariant(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df).theme_plain()
        assert t.render("typst") == t.render("typst")

    def test_render_does_not_mutate_resolution_state(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df)
        state = (len(t._style_directives), len(t._format_directives))

        first = t.render("typst")
        second = t.render("typst")

        assert first == second
        assert (len(t._style_directives), len(t._format_directives)) == state

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
        assert_snapshot("basic_typ", tt(df).theme_plain().render("typst"))

    def test_basic_3x3(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        assert_snapshot("basic_3x3", tt(df).theme_plain().render("typst"))


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_empty_dataframe_renders_with_all_backends(output):
    df = pl.DataFrame(schema={"A": pl.Int64, "B": pl.String})
    rendered = tt(df).theme_plain().render(output)
    assert rendered
    assert "A" in rendered
    assert "B" in rendered


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_unicode_text_survives_all_renderers(output):
    values = ["日本語", "table 🎉", "مرحبا", "e\u0301"]
    rendered = tt(pl.DataFrame({"text": values})).theme_plain().render(output)
    for value in values:
        assert value in rendered


@pytest.mark.parametrize(("suffix", "output"), [(".typ", "typst"), (".html", "html")])
def test_save_plain_output(tmp_path, suffix, output):
    table = tt(pl.DataFrame({"A": [1], "B": [2]})).theme_plain()
    expected = table.render(output)
    destination = tmp_path / f"output{suffix}"
    table.save(str(destination))
    assert destination.read_text(encoding="utf-8") == expected


def test_build_rejects_unknown_output():
    table = tt(pl.DataFrame({"A": [1]})).theme_plain()
    with pytest.raises(NotImplementedError, match="output='markdown' not implemented"):
        build(table, "markdown")


def test_render_rejects_unknown_output():
    table = tt(pl.DataFrame({"A": [1]})).theme_plain()
    with pytest.raises(NotImplementedError, match="output='markdown' not implemented"):
        table.render("markdown")


def test_save_adds_context_to_table_write_failure(tmp_path):
    destination = tmp_path / "output.typ"
    destination.mkdir()

    with pytest.raises(OSError, match=r"could not write table file .*output\.typ"):
        tt(pl.DataFrame({"A": [1]})).save(str(destination))


class TestDefaultAlignment:
    def test_infers_alignment_from_source_dtypes(self):
        df = pl.DataFrame(
            schema={
                "text": pl.String,
                "integer": pl.Int64,
                "unsigned": pl.UInt32,
                "float": pl.Float64,
                "decimal": pl.Decimal,
                "boolean": pl.Boolean,
                "date": pl.Date,
                "duration": pl.Duration,
            }
        )

        built = build(tt(df).theme_plain(), "typst")

        assert built.column_alignments == ["l", "r", "r", "r", "r", "l", "l", "l"]

    def test_typst_uses_column_defaults_for_header_and_body(self):
        df = pl.DataFrame({"label": ["A"], "number": [123]})

        out = tt(df).theme_plain().render("typst")

        assert "else { (left, right).at(x) }" in out

    def test_html_aligns_numeric_header_and_body(self):
        df = pl.DataFrame({"label": ["A"], "number": [123]})

        out = tt(df).theme_plain().render("html")

        assert "<th>label</th>" in out
        assert '<th style="text-align:right">number</th>' in out
        assert "<td>A</td>" in out
        assert '<td style="text-align:right">123</td>' in out

    def test_ascii_aligns_numeric_header_and_body(self):
        out = tt(pl.DataFrame({"n": [123]})).theme_plain().render("ascii")

        assert "|   n |" in out
        assert "| 123 |" in out

    def test_fmt_does_not_change_numeric_alignment(self):
        table = (
            tt(pl.DataFrame({"number": [1.25]}))
            .theme_plain()
            .fmt(j="number", fn=lambda values: [f"${value}" for value in values])
        )

        assert build(table, "typst").column_alignments == ["r"]
        assert "else { (right,).at(x) }" in table.render("typst")

    def test_explicit_style_overrides_default(self):
        table = tt(pl.DataFrame({"number": [123]})).theme_plain().style(j="number", align="l")
        built = build(table, "typst")

        assert (0, 0) not in built.style_grid
        assert built.style_grid[(1, 0)]["align"] == "l"
        assert '<td style="text-align:left">123</td>' in table.render("html")
        assert "| 123    |" in table.render("ascii")

    def test_numeric_row_group_label_stays_left_aligned(self):
        table = tt(pl.DataFrame({"number": [1, 2]})).theme_plain().group(i={"Group": 0})
        built = build(table, "typst")
        group_row = built.layout.groupi_rows[0]

        assert built.style_grid[(group_row, 0)]["align"] == "l"


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
        out = tt(df).theme_plain().render("typst")
        assert "caption:" not in out
        assert_snapshot("basic_typ", out)

    def test_label_attached_to_figure(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, label="results-table").theme_plain().render("typst")
        assert out.endswith(") <results-table>")

    def test_figure_false_emits_table_without_figure(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, figure=False).theme_plain().style(i=0, bold=True).render("typst")
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
        table = tt(df, caption="Results").theme_plain()
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
