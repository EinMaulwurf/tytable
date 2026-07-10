import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tinytables import tt
from tinytables._escape import escape_typst

EXPECTED_BASIC_TYP = (
    "#show figure: set block(breakable: false)\n"
    "#figure(\n"
    '  kind: "tinytable",\n'
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


@pytest.mark.typst
class TestByteExact:
    def test_byte_exact_acceptance(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        result = tt(df, theme=None).render("typst")
        assert result == EXPECTED_BASIC_TYP

    def test_invariant(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        t = tt(df, theme=None)
        assert t.render("typst") == t.render("typst")

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
        assert_snapshot("basic_typ", tt(df, theme=None).render("typst"))

    def test_basic_3x3(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        assert_snapshot("basic_3x3", tt(df, theme=None).render("typst"))


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
        out = tt(df, theme=None).render("typst")
        assert "caption:" not in out
        assert_snapshot("basic_typ", out)


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

    def test_hash_escaped(self):
        assert escape_typst("#") == "\\#"

    def test_bracket_escaped(self):
        assert escape_typst("[") == "\\["

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
