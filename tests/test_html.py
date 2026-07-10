import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tinytables import tt
from tinytables._escape import escape_html


@pytest.mark.html
class TestBasicHtml:
    def test_basic_2x2(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, theme=None).render("html")
        assert out.startswith("<table")
        assert out.endswith("</table>")
        assert "<td>1</td>" in out
        assert_snapshot("html_basic_2x2", out)

    def test_basic_3x3(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        out = tt(df, theme=None).render("html")
        assert_snapshot("html_basic_3x3", out)

    def test_repr_html(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        tab = tt(df, theme=None)
        html = tab._repr_html_()
        assert html.startswith("<table")
        assert html.endswith("</table>")

    def test_caption(self):
        df = pl.DataFrame({"A": [1]})
        out = tt(df, caption="My Table").render("html")
        assert "<caption>My Table</caption>" in out
        assert_snapshot("html_caption", out)

    def test_no_colnames(self):
        df = pl.DataFrame({"A": [1, 3]})
        out = tt(df, colnames=False).render("html")
        assert "<thead>" not in out
        assert_snapshot("html_no_colnames", out)


@pytest.mark.html
class TestHtmlStyle:
    def test_bold(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, bold=True).render("html")
        assert "font-weight:bold" in out
        assert_snapshot("html_style_bold", out)

    def test_italic(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, italic=True).render("html")
        assert "font-style:italic" in out

    def test_underline(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, underline=True).render("html")
        assert "text-decoration:underline" in out

    def test_color_and_background(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, color="#ff0000", background="#ffffcc").render("html")
        assert "color:#ff0000" in out
        assert "background-color:#ffffcc" in out
        assert_snapshot("html_style_color", out)

    def test_align(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, align="c").render("html")
        assert "text-align:center" in out

    def test_fontsize(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(df).style(i=0, j=0, fontsize=1.2).render("html")
        assert "font-size:1.2em" in out

    def test_column_style(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df).style(j="A", italic=True).render("html")
        assert out.count("font-style:italic") == 3


@pytest.mark.html
class TestHtmlGrouping:
    def test_col_group(self):
        df = pl.DataFrame({"Region": ["East"], "Sales": [100]})
        out = tt(df, theme=None).group(j={"Group": ["Region", "Sales"]}).render("html")
        assert "Group" in out
        assert 'colspan="2"' in out
        assert_snapshot("html_group_col", out)

    def test_row_group(self):
        df = pl.DataFrame({"A": [1, 2, 3]})
        out = tt(df, theme=None).group(i={"First": 0, "Second": 2}).render("html")
        assert "First" in out
        assert "Second" in out
        assert_snapshot("html_group_row", out)


@pytest.mark.html
class TestHtmlNotes:
    def test_footnote_targeted(self):
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        out = tt(df, theme=None, notes=[{"text": "Note", "i": [0], "j": ["A"]}]).render("html")
        assert "<tfoot>" in out
        assert "<sup>1</sup>" in out
        assert_snapshot("html_footnote", out)

    def test_footnote_multiple(self):
        df = pl.DataFrame({"A": [1, 2]})
        out = tt(
            df,
            theme=None,
            notes=[
                {"text": "First note", "i": [0], "j": ["A"]},
                {"text": "Second note", "i": [1], "j": ["A"]},
            ],
        ).render("html")
        assert "First note" in out
        assert "Second note" in out


@pytest.mark.html
class TestHtmlEscape:
    def test_brackets_escaped(self):
        df = pl.DataFrame({"A": ["x<y"]})
        out = tt(df, theme=None).render("html")
        assert "&lt;" in out

    def test_ampersand_escaped(self):
        df = pl.DataFrame({"A": ["a&b"]})
        out = tt(df, theme=None).render("html")
        assert "&amp;" in out

    def test_html_escape_helper(self):
        assert escape_html("<tag>") == "&lt;tag&gt;"
        assert escape_html("a&b") == "a&amp;b"
        assert escape_html("plain") == "plain"


@pytest.mark.html
class TestHtmlOutputGating:
    def test_html_only_style_visible_in_html(self):
        df = pl.DataFrame({"A": [1]})
        out = tt(df).style(i=0, background="#ff0000", output=("html",)).render("html")
        assert "background-color:#ff0000" in out

    def test_html_only_style_invisible_in_typst(self):
        df = pl.DataFrame({"A": [1]})
        out = tt(df).style(i=0, background="#ff0000", output=("html",)).render("typst")
        assert "#ff0000" not in out


@pytest.mark.html
class TestAscii:
    def test_basic_ascii(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, theme=None).render("ascii")
        assert "+---+---+" in out
        assert "| A | B |" in out
        assert "| 1 | 2 |" in out
        assert "| 3 | 4 |" in out
        assert_snapshot("ascii_basic", out)

    def test_no_colnames_ascii(self):
        df = pl.DataFrame({"A": [1, 3]})
        out = tt(df, colnames=False).render("ascii")
        assert "+---+" in out
        assert "| 1 |" in out

    def test_repr_ascii(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        tab = tt(df, theme=None)
        r = repr(tab)
        assert "+---+---+" in r

    def test_wide_cell_truncate(self):
        df = pl.DataFrame({"A": ["x" * 70]})
        out = tt(df, theme=None).render("ascii")
        assert "…" in out


@pytest.mark.html
class TestHtmlBorders:
    def test_default_theme_borders_on_correct_rows(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, theme="default").render("html")
        lines = out.splitlines()
        # Header row should have top (0.08em) and bottom (0.05em) borders
        header_line = [ln for ln in lines if "<th" in ln and "border" in ln][0]
        assert "border-top:0.08em" in header_line
        assert "border-bottom:0.05em" in header_line
        # Last data row should have bottom (0.08em) border
        body_lines = [ln for ln in lines if "<td" in ln and "border" in ln]
        assert any("border-bottom:0.08em" in ln for ln in body_lines)

    def test_explicit_line_on_header(self):
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        out = tt(df, theme=None).style(i="header", line="b").render("html")
        header_line = [ln for ln in out.splitlines() if "<th" in ln and "border" in ln]
        assert len(header_line) == 1
        assert "border-bottom:0.1em" in header_line[0]

    def test_explicit_line_on_body_row(self):
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        out = tt(df, theme=None).style(i=1, line="b").render("html")
        body_lines = [ln for ln in out.splitlines() if "<td" in ln and "border" in ln]
        assert any("border-bottom:0.1em" in ln for ln in body_lines)


@pytest.mark.html
class TestHtmlWidth:
    def test_scalar_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=0.8).render("html")
        assert "width:80.00%" in out

    def test_list_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=[0.3, 0.7]).render("html")
        assert "<colgroup>" in out
        assert "width:30.00%" in out
        assert "width:70.00%" in out

    def test_string_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width="5cm").render("html")
        assert "width:5cm" in out

    def test_list_with_none_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=["5cm", None]).render("html")
        assert "width:5cm" in out
        assert "<col>" in out


@pytest.mark.typst
class TestTypstWidth:
    def test_scalar_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=0.8).render("typst")
        assert "40.00%" in out

    def test_list_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=[0.3, 0.7]).render("typst")
        assert "30.00%" in out
        assert "70.00%" in out

    def test_no_width_uses_auto(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None).render("typst")
        assert "columns: (auto, auto)" in out

    def test_string_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width="5cm").render("typst")
        assert "columns: (5cm, 5cm)" in out

    def test_mixed_list_width(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, theme=None, width=["5cm", None]).render("typst")
        assert "columns: (5cm, auto)" in out

    def test_list_with_none_width(self):
        df = pl.DataFrame({"A": [1], "B": [2], "C": [3]})
        out = tt(df, theme=None, width=[0.3, None, "2cm"]).render("typst")
        assert "columns: (30.00%, auto, 2cm)" in out

    def test_finalize_callback(self):
        df = pl.DataFrame({"A": [1]})
        out = tt(df, theme=None).finalize(lambda s, o: s.upper()).render("typst")
        assert out == tt(df, theme=None).render("typst").upper()

    def test_finalize_receives_output(self):
        df = pl.DataFrame({"A": [1]})
        calls = []
        tt(df, theme=None).finalize(lambda s, o: calls.append(o) or s).render("typst")
        assert calls == ["typst"]


@pytest.mark.typst
class TestTypstGutter:
    def test_default_gutter(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df).group(j={"G": [0, 1]}).render("typst")
        assert "column-gutter: 2pt," in out

    def test_custom_gutter(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, gutter=5).group(j={"G": [0, 1]}).render("typst")
        assert "column-gutter: 5pt," in out

    def test_string_gutter(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, gutter="0.1em").group(j={"G": [0, 1]}).render("typst")
        assert "column-gutter: 0.1em," in out

    def test_zero_gutter(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, gutter=0).group(j={"G": [0, 1]}).render("typst")
        assert "column-gutter: 0pt," in out

    def test_none_gutter_omitted(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        out = tt(df, gutter=None).group(j={"G": [0, 1]}).render("typst")
        assert "column-gutter" not in out
