import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._render_typst import _props_to_signature
from tytable._resolve import build

DF = pl.DataFrame({"A": [1, 3], "B": [2, 4]})


@pytest.mark.typst
class TestStyleProps:
    def test_bold(self):
        out = tt(DF).style(i=0, j=0, bold=True).render("typst")
        assert "(bold: true,)" in out
        assert '"1_0": 0' in out
        assert_snapshot("style_bold", out)

    def test_italic(self):
        out = tt(DF).style(i=0, j=0, italic=True).render("typst")
        assert "(italic: true,)" in out
        assert_snapshot("style_italic", out)

    def test_underline(self):
        out = tt(DF).style(i=0, j=0, underline=True).render("typst")
        assert "(underline: true,)" in out
        assert_snapshot("style_underline", out)

    def test_strikeout(self):
        out = tt(DF).style(i=0, j=0, strikeout=True).render("typst")
        assert "(strikeout: true,)" in out
        assert_snapshot("style_strikeout", out)

    def test_monospace(self):
        out = tt(DF).style(i=0, j=0, monospace=True).render("typst")
        assert "(mono: true,)" in out
        assert_snapshot("style_mono", out)

    def test_smallcaps(self):
        out = tt(DF).style(i=0, j=0, smallcaps=True).render("typst")
        assert "(smallcaps: true,)" in out
        assert_snapshot("style_smallcaps", out)

    def test_color(self):
        out = tt(DF).style(i=0, j=0, color="#ff0000").render("typst")
        assert 'color: rgb("#ff0000")' in out
        assert_snapshot("style_color", out)

    def test_background(self):
        out = tt(DF).style(i=0, j=0, background="#ffffcc").render("typst")
        assert 'background: rgb("#ffffcc")' in out
        built = build(tt(DF).style(i=0, j=0, background="#ffffcc"), "typst")
        assert built.has_background is True
        assert_snapshot("style_background", out)

    def test_fontsize(self):
        out = tt(DF).style(i=0, j=0, fontsize=1.2).render("typst")
        assert "fontsize: 1.2em" in out
        assert_snapshot("style_fontsize", out)

    def test_indent(self):
        out = tt(DF).style(i=0, j=0, indent=0.5).render("typst")
        assert "indent: 0.5em" in out
        assert_snapshot("style_indent", out)

    def test_indent_zero_not_emitted(self):
        out = tt(DF).style(i=0, j=0, indent=0).render("typst")
        assert "indent:" not in out

    def test_rotate(self):
        out = tt(DF).style(i=0, j=0, rotate=90).render("typst")
        assert "rotate: 90deg" in out
        assert_snapshot("style_rotate", out)

    def test_rotate_negative(self):
        out = tt(DF).style(i=0, j=0, rotate=-90).render("typst")
        assert "rotate: -90deg" in out

    def test_rotate_header(self):
        out = tt(DF).style(i="header", rotate=90).render("typst")
        assert "rotate: 90deg" in out
        assert '"0_0": 0' in out
        assert '"0_1": 0' in out
        assert_snapshot("style_rotate_header", out)

    def test_rotate_header_specific_column(self):
        out = tt(DF).style(i="header", j="A", rotate=90).render("typst")
        assert "rotate: 90deg" in out
        assert '"0_0": 0' in out
        assert '"0_1": 0' not in out

    def test_rotate_in_show_rule(self):
        out = tt(DF).style(i="header", rotate=90).render("typst")
        assert "align(a, rotate(style.rotate, reflow: true, tmp))" in out

    def test_rotate_with_align_emit_signatures(self):
        out = tt(DF).style(i="header", rotate=90, align="l", alignv="b").render("typst")
        assert "rotate: 90deg" in out
        assert "align: left + bottom" in out
        assert "align(a, rotate(style.rotate, reflow: true, tmp))" in out

    def test_rotate_not_emitted_when_none(self):
        out = tt(DF, theme=None).render("typst")
        assert "rotate:" not in out

    def test_align(self):
        out = tt(DF).style(i=0, j=0, align="c").render("typst")
        assert "align: center" in out
        assert_snapshot("style_align", out)

    def test_alignv(self):
        out = tt(DF).style(i=0, j=0, alignv="m").render("typst")
        assert "align: horizon" in out
        assert_snapshot("style_alignv", out)

    def test_align_combined(self):
        out = tt(DF).style(i=0, j=0, align="c", alignv="m").render("typst")
        assert "align: center + horizon" in out
        assert_snapshot("style_align_combined", out)

    def test_color_normalization_3hex(self):
        out = tt(DF).style(i=0, j=0, color="#f00").render("typst")
        assert 'rgb("#ff0000")' in out

    def test_color_8hex_alpha(self):
        out = tt(DF).style(i=0, j=0, color="#ff000080").render("typst")
        assert 'rgb("#ff000080")' in out

    def test_background_8hex_alpha(self):
        out = tt(DF).style(i=0, j=0, background="#00ff0033").render("typst")
        assert 'background: rgb("#00ff0033")' in out

    def test_color_normalization_4hex_alpha(self):
        out = tt(DF).style(i=0, j=0, color="#f008").render("typst")
        assert 'rgb("#ff000088")' in out

    def test_named_color(self):
        out = tt(DF).style(i=0, j=0, color="red").render("typst")
        assert 'rgb("#ff0000")' in out

    def test_black_built_in(self):
        out = tt(DF).style(i=0, j=0, color="black").render("typst")
        assert "color: black" in out
        assert "rgb" not in out

    def test_typst_color_function(self):
        out = tt(DF).style(i=0, j=0, color="luma(50%)").render("typst")
        assert "color: luma(50%)" in out

    @pytest.mark.parametrize("prop", ["color", "background", "line_color"])
    @pytest.mark.parametrize(
        "value",
        [
            "red), pagebreak(), rgb(",
            "red;background:url(https://example.invalid)",
            'red"><script>alert(1)</script>',
        ],
    )
    def test_unsafe_color_value_rejected(self, prop, value):
        with pytest.raises(ValueError, match=f"invalid {prop}"):
            tt(DF, theme=None).style(**{prop: value})

    @pytest.mark.parametrize("value", ["left#", "left()", "left;", "left[]"])
    def test_typst_signature_rejects_unsafe_string_properties(self, value):
        with pytest.raises(ValueError, match="unsafe Typst style property 'align'"):
            _props_to_signature({"align": value})


@pytest.mark.typst
class TestOverwriteSemantics:
    def test_different_props_both_present(self):
        out = tt(DF).style(i=0, j=0, bold=True).style(i=0, j=0, italic=True).render("typst")
        assert "(bold: true, italic: true,)" in out
        assert '"1_0": 0' in out

    def test_same_prop_last_wins(self):
        out = (
            tt(DF).style(i=0, j=0, color="#ff0000").style(i=0, j=0, color="#00ff00").render("typst")
        )
        assert 'rgb("#00ff00")' in out
        assert 'rgb("#ff0000")' not in out


@pytest.mark.typst
class TestTargeting:
    def test_header_styling(self):
        out = tt(DF).style(i="header", bold=True).render("typst")
        assert '"0_0": 0' in out
        assert '"0_1": 0' in out
        assert_snapshot("style_header", out)

    def test_row_targeting(self):
        out = tt(DF).style(i=1, bold=True).render("typst")
        assert '"2_0": 0' in out
        assert '"2_1": 0' in out

    def test_column_targeting_by_name(self):
        out = tt(DF).style(j="B", italic=True).render("typst")
        assert '"0_1": 0' in out
        assert '"1_1": 0' in out
        assert '"2_1": 0' in out

    def test_cell_targeting(self):
        out = tt(DF).style(i=0, j=1, bold=True).render("typst")
        assert '"1_1": 0' in out
        assert '"1_0"' not in out


@pytest.mark.typst
class TestAppendVsOverwrite:
    def test_non_line_props_overwrite(self):
        t = tt(DF, theme=None).style(i=0, j=0, bold=True).style(i=0, j=0, bold=False)
        built = build(t, "typst")
        assert built.style_grid[(1, 1)] == {"bold": False}

    def test_line_props_append(self):
        t = tt(DF, theme=None).style(i=0, j=0, line="t").style(i=0, j=0, line="l")
        built = build(t, "typst")
        assert len(built.style_lines) == 2


@pytest.mark.typst
class TestOutputGating:
    def test_html_only_directive_skipped_for_typst(self):
        out = tt(DF, theme=None).style(i=0, j=0, bold=True, output=("html",)).render("typst")
        assert "(bold: true,)" not in out
        assert out == tt(DF, theme=None).render("typst")


@pytest.mark.typst
class TestStyleValidation:
    def test_bad_align(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, align="x")

    def test_bad_alignv(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, alignv="z")

    def test_bad_line(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, line="z")

    def test_colspan_must_be_positive(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, colspan=0)

    def test_color_must_be_str(self):
        with pytest.raises(TypeError):
            tt(DF).style(i=0, color=(1, 2, 3))

    def test_rotate_must_be_number(self):
        with pytest.raises(TypeError):
            tt(DF).style(i=0, rotate="90")

    def test_negative_line_width(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, line="t", line_width=-1)

    def test_bad_multi_char_align(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, j=[0, 1], align="lx")

    def test_bad_multi_char_alignv(self):
        with pytest.raises(ValueError):
            tt(DF).style(i=0, j=[0, 1], alignv="tz")


@pytest.mark.typst
class TestBordersLines:
    def test_line_top(self):
        out = tt(DF).style(i=0, line="t").render("typst")
        assert_snapshot("line_top", out)

    def test_line_bottom(self):
        out = tt(DF).style(i=1, line="b").render("typst")
        assert_snapshot("line_bottom", out)

    def test_line_left(self):
        out = tt(DF).style(j=0, line="l").render("typst")
        assert_snapshot("line_left", out)

    def test_line_right(self):
        out = tt(DF).style(j=1, line="r").render("typst")
        assert_snapshot("line_right", out)

    def test_line_tblr(self):
        out = tt(DF).style(i=0, j=0, line="tblr").render("typst")
        assert_snapshot("line_tblr", out)

    def test_line_color(self):
        out = tt(DF).style(i=0, line="t", line_color="#ff0000").render("typst")
        assert 'rgb("#ff0000")' in out
        assert_snapshot("line_color", out)

    def test_line_width(self):
        out = tt(DF).style(i=0, line="t", line_width=0.5).render("typst")
        assert "0.5em" in out
        assert_snapshot("line_width", out)

    def test_chunking_non_consecutive_columns(self):
        out = tt(DF).style(i=0, j=[0, 2], line="t").render("typst")
        assert_snapshot("line_chunking", out)

    def test_dedupe_duplicate_line_directives(self):
        out = tt(DF).style(i=0, j=0, line="t").style(i=0, j=0, line="t").render("typst")
        assert_snapshot("line_dedupe", out)

    def test_dedupe_top_bottom_merge(self):
        out = tt(DF).style(i=0, line="b").style(i=1, j=0, line="t").render("typst")
        assert_snapshot("line_dedupe_tb_merge", out)

    def test_default_stroke(self):
        out = tt(DF).style(i=0, line="t").render("typst")
        assert "0.1em + black" in out

    def test_no_lines_default(self):
        out = tt(DF, theme=None).render("typst")
        assert "table.hline" not in out
        assert "table.vline" not in out


@pytest.mark.typst
class TestCaptionNotesStyle:
    def test_caption_bold_color_fontsize(self):
        out = (
            tt(DF, caption="Demo")
            .style(i="caption", bold=True, color="#c0392b", fontsize=1.2)
            .render("typst")
        )
        assert 'caption: text(size: 1.2em, fill: rgb("#c0392b"), weight: "bold", [Demo]),' in out
        assert_snapshot("caption_bold_color_fontsize", out)

    def test_caption_italic_smallcaps(self):
        out = tt(DF, caption="Demo").style(i="caption", italic=True, smallcaps=True).render("typst")
        assert 'style: "italic"' in out
        assert 'smallcaps(text(style: "italic", [Demo]))' in out
        assert_snapshot("caption_italic_smallcaps", out)

    def test_notes_italic_color(self):
        out = (
            tt(DF, notes=["Source: data"])
            .style(i="notes", italic=True, color="blue")
            .render("typst")
        )
        assert '#text(fill: rgb("#0000ff"), style: "italic", [Source: data])' in out
        assert_snapshot("notes_italic_color", out)

    def test_notes_with_marker_styled(self):
        out = (
            tt(DF, notes=[{"text": "p < 0.05", "marker": "*"}])
            .style(i="notes", bold=True, color="#c0392b")
            .render("typst")
        )
        assert "[#super[\\*] #text" in out
        assert_snapshot("notes_marker_styled", out)

    def test_notes_align_override(self):
        out = tt(DF, notes=["Note one"]).style(i="notes", align="c", italic=True).render("typst")
        assert "align: center, colspan: 2" in out
        assert_snapshot("notes_align_center", out)

    def test_caption_unstyled_unchanged(self):
        out = tt(DF, caption="Demo").render("typst")
        assert "caption: text([Demo])," in out

    def test_notes_unstyled_unchanged(self):
        out = tt(DF, notes=["Source: data"]).render("typst")
        assert "table.cell(align: left, colspan: 2, [Source: data])," in out

    def test_output_filter_typst_only(self):
        t = tt(DF, caption="Demo").style(i="caption", bold=True, output=("typst",))
        assert 'weight: "bold"' in t.render("typst")
        html = t.render("html")
        assert "<b>" not in html

    def test_output_filter_html_only(self):
        t = tt(DF, caption="Demo").style(i="caption", bold=True, output=("html",))
        typst = t.render("typst")
        assert 'weight: "bold"' not in typst
        assert "<b>Demo</b>" in t.render("html")

    def test_multiple_style_calls_combine(self):
        out = (
            tt(DF, caption="Demo")
            .style(i="caption", bold=True)
            .style(i="caption", italic=True, color="#c0392b")
            .render("typst")
        )
        assert 'weight: "bold"' in out
        assert 'style: "italic"' in out
        assert 'rgb("#c0392b")' in out

    def test_meta_style_does_not_affect_grid(self):
        out = (
            tt(DF)
            .style(i="caption", bold=True)
            .style(i="notes", italic=True)
            .style(i=0, j=0, bold=True)
            .render("typst")
        )
        # Grid styling for body cell still present.
        assert '"1_0": 0' in out


@pytest.mark.typst
class TestListSelectors:
    def test_column_style_by_list_of_names(self):
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4], "C": [5, 6]})
        out = tt(df).style(j=["A", "C"], bold=True).render("typst")
        assert "(bold: true,)" in out
        assert '"1_0": 0' in out
        assert '"2_0": 0' in out
        assert '"1_2": 0' in out
        assert '"2_2": 0' in out
        assert '"1_1": 0' not in out
        assert '"2_1": 0' not in out

    def test_column_fmt_by_list_of_names(self):
        df = pl.DataFrame({"x": [3.141, 2.718], "y": [1.0, 2.0], "z": [3.0, 4.0]})
        out = tt(df).fmt(j=["x", "z"], digits=1).render("typst")
        assert "3.1" in out
        assert "2.7" in out
        assert "1" in out

    def test_i_list_of_strings(self):
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        out = tt(df).style(i=["header", "body"], italic=True).render("typst")
        assert "(italic: true,)" in out
        assert '"0_0": 0' in out
        assert '"1_0": 0' in out
        assert '"2_0": 0' in out


@pytest.mark.typst
class TestDataDrivenRowSelectors:
    DF = pl.DataFrame({"Score": [95, 72, 88, 60], "Grade": ["A", "C", "B", "D"]})

    def test_polars_expr_style(self):
        out = tt(self.DF).style(i=pl.col("Score") > 80, bold=True).render("typst")
        assert "(bold: true,)" in out
        assert '"1_0": 0' in out
        assert '"1_1": 0' in out
        assert '"3_0": 0' in out
        assert '"3_1": 0' in out
        assert '"2_0": 0' not in out
        assert '"4_0": 0' not in out

    def test_polars_series_style(self):
        mask = pl.Series("m", [False, True, False, True])
        out = tt(self.DF).style(i=mask, italic=True).render("typst")
        assert "(italic: true,)" in out
        assert '"2_0": 0' in out
        assert '"4_0": 0' in out
        assert '"1_0": 0' not in out

    def test_callable_style(self):
        out = (
            tt(self.DF)
            .style(i=lambda row: row["Grade"] in ("A", "B"), color="blue")
            .render("typst")
        )
        assert "color: rgb" in out
        assert '"1_0"' in out
        assert '"3_0"' in out
        assert '"2_0"' not in out

    def test_polars_expr_fmt(self):
        out = tt(self.DF).fmt(i=pl.col("Score") < 70, digits=0).render("typst")
        assert "[72]" in out
        assert "[60]" in out

    def test_data_driven_with_row_groups(self):
        df = pl.DataFrame({"v": [10, 20, 30]})
        out = tt(df).group(i={"Mid": 1}).style(i=pl.col("v") > 15, bold=True).render("typst")
        assert "20" in out
        assert "30" in out
        assert "(bold: true,)" in out
        style_dict = out[out.index("style-dict") : out.index("style-array")]
        assert '"3_0"' in style_dict
        assert '"4_0"' in style_dict

    def test_no_match_renders_fine(self):
        out = tt(self.DF).style(i=pl.col("Score") > 200, bold=True).render("typst")
        assert "95" in out
        assert "72" in out

    def test_match_all_works(self):
        out = tt(self.DF).style(i=pl.col("Score") > 0, italic=True).render("typst")
        assert out.count("(italic: true,)") >= 1


@pytest.mark.typst
class TestPerColumnAlign:
    """Per-column alignment via multi-char strings like ``align="llr"``."""

    DF3 = pl.DataFrame({"A": [1, 4], "B": [2, 5], "C": [3, 6]})

    def test_align_j_list(self):
        t = tt(self.DF3, theme=None).style(i=0, j=[0, 1, 2], align="lcr")
        built = build(t, "typst")
        assert built.style_grid[(1, 1)]["align"] == "l"
        assert built.style_grid[(1, 2)]["align"] == "c"
        assert built.style_grid[(1, 3)]["align"] == "r"

    def test_align_all_rows(self):
        t = tt(self.DF3, theme=None).style(j=[0, 1, 2], align="lcr")
        built = build(t, "typst")
        for i in (0, 1, 2):
            assert built.style_grid[(i, 1)]["align"] == "l"
            assert built.style_grid[(i, 2)]["align"] == "c"
            assert built.style_grid[(i, 3)]["align"] == "r"

    def test_alignv_j_list(self):
        t = tt(self.DF3, theme=None).style(i=0, j=[0, 1, 2], alignv="tmb")
        built = build(t, "typst")
        assert built.style_grid[(1, 1)]["alignv"] == "t"
        assert built.style_grid[(1, 2)]["alignv"] == "m"
        assert built.style_grid[(1, 3)]["alignv"] == "b"

    def test_align_implicit_all_columns(self):
        t = tt(self.DF3, theme=None).style(i=0, align="lcr")
        built = build(t, "typst")
        assert built.style_grid[(1, 1)]["align"] == "l"
        assert built.style_grid[(1, 2)]["align"] == "c"
        assert built.style_grid[(1, 3)]["align"] == "r"

    def test_align_single_value_broadcasts(self):
        t = tt(self.DF3, theme=None).style(i=0, j=[0, 1, 2], align="r")
        built = build(t, "typst")
        for j in (1, 2, 3):
            assert built.style_grid[(1, j)]["align"] == "r"

    def test_align_and_alignv_per_column(self):
        df = pl.DataFrame({"A": [1], "B": [2]})
        t = tt(df, theme=None).style(i=0, j=[0, 1], align="lr", alignv="tm")
        built = build(t, "typst")
        assert built.style_grid[(1, 1)]["align"] == "l"
        assert built.style_grid[(1, 1)]["alignv"] == "t"
        assert built.style_grid[(1, 2)]["align"] == "r"
        assert built.style_grid[(1, 2)]["alignv"] == "m"

    def test_align_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="3 chars but 2 column"):
            tt(self.DF3).style(i=0, j=[0, 1], align="lcr").render("typst")

    def test_align_too_long_for_single_col(self):
        with pytest.raises(ValueError, match="2 chars but 1 column"):
            tt(self.DF3).style(i=0, j=0, align="lr").render("typst")

    def test_align_renders_typst(self):
        out = tt(self.DF3).style(i=0, j=[0, 1, 2], align="lcr").render("typst")
        assert "align: left" in out
        assert "align: center" in out
        assert "align: right" in out

    def test_align_snapshot(self):
        out = tt(self.DF3).style(i=0, j=[0, 1, 2], align="lcr").render("typst")
        assert_snapshot("style_align_per_column", out)

    def test_align_meta_selector_rejects_per_column(self):
        with pytest.raises(ValueError, match="per-column align"):
            tt(DF).style(i="caption", align="lr").render("typst")
