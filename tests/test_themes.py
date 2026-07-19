import polars as pl
import polars.selectors as cs
import pytest

from tests.helpers import assert_snapshot
from tytable import TyTable, tt
from tytable._resolve import build

DF = pl.DataFrame({"A": [1, 3], "B": [2, 4]})


@pytest.mark.typst
class TestThemeDefault:
    def test_empty_table_styles_only_visible_header_boundaries(self):
        built = build(tt(pl.DataFrame(schema={"A": pl.Int64})), "typst")
        assert [(line["i"], line["line"], line["line_width"]) for line in built.style_lines] == [
            (0, "t", 0.08),
            (0, "b", 0.05),
        ]

    def test_booktab_rules(self):
        out = tt(DF).render("typst")
        assert out.count("table.hline") == 3
        assert "0.08em" in out
        assert "0.05em" in out
        assert_snapshot("theme_default", out)

    def test_no_colnames_still_top_and_bottom(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, colnames=False).render("typst")
        assert out.count("table.hline") == 2
        assert_snapshot("theme_default_no_colnames", out)

    def test_with_col_groups(self):
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": [7, 8]})
        out = tt(df).group(j={"Group": [0, 1]}).render("typst")
        assert out.count("table.hline") == 3
        assert_snapshot("theme_default_with_groups", out)


@pytest.mark.typst
class TestThemeStriped:
    def test_even_row_background(self):
        out = tt(DF).theme_striped().render("typst")
        assert "#ededed" in out
        assert "table.hline" not in out
        assert_snapshot("theme_striped", out)

    def test_three_rows(self):
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        out = tt(df).theme_striped().render("typst")
        assert_snapshot("theme_striped_3rows", out)

    def test_stripes_follow_source_rows_across_group_separators(self):
        df = pl.DataFrame({"A": [1, 2, 3]})
        table = tt(df).group(i={"before": 0, "middle": 2}).theme_striped()
        built = build(table, "typst")
        striped_rows = {i for (i, _), props in built.style_grid.items() if "background" in props}
        assert striped_rows == {2, 5}


@pytest.mark.typst
class TestThemeGrid:
    def test_grid_stroke_and_lines(self):
        out = tt(DF).theme_grid().render("typst")
        assert "(paint: black)" in out
        assert "table.hline" in out
        assert "table.vline" in out
        assert_snapshot("theme_grid", out)

    def test_grid_targets_structural_and_data_rows(self):
        table = tt(DF).group(i={"group": 1}).group(j={"all": ["A", "B"]}).theme_grid()
        built = build(table, "typst")
        assert {(line["i"], line["j"]) for line in built.style_lines} == {
            (i, j) for i in range(5) for j in range(2)
        }


@pytest.mark.typst
class TestThemePlain:
    def test_preserves_recorded_intent(self):
        t = tt(DF).style(i=0, bold=True).fmt(j="A", digits=1)
        assert len(t._style_directives) == 1
        assert len(t._format_directives) == 1
        t.theme_plain()
        assert len(t._style_directives) == 1
        assert len(t._format_directives) == 1

    def test_no_lines_in_output(self):
        out = tt(DF).theme_plain().render("typst")
        assert "table.hline" not in out
        assert "table.vline" not in out
        assert_snapshot("theme_plain", out)

    def test_preserves_constructor_and_layout_options(self):
        t = tt(DF, figure=False, height=1.5, gutter="0.2em").theme_plain()
        assert t._typst_opts.figure is False
        assert t._typst_opts.row_height_em == 1.5
        assert t._typst_opts.column_gutter == "0.2em"

    def test_call_order_does_not_erase_styles_or_formats(self):
        before = tt(DF).theme_plain().style(i=0, bold=True).fmt(j="A", digits=1)
        after = tt(DF).style(i=0, bold=True).fmt(j="A", digits=1).theme_plain()
        assert before.render("typst") == after.render("typst")


@pytest.mark.typst
class TestThemeRotate:
    def test_whole_table_rotate(self):
        out = tt(DF).rotate().render("typst")
        assert "#rotate(90" in out
        assert_snapshot("rotate", out)

    def test_selected_cell_rotate(self):
        out = tt(DF).style(i="header", j="A", rotate=45).render("typst")
        assert "rotate: 45deg" in out
        assert "#rotate(45deg, reflow: true" not in out


@pytest.mark.typst
class TestThemeResize:
    def test_default_full_width_both(self):
        out = tt(DF).resize().render("typst")
        assert "#layout(size => {" in out
        assert "let body = [" in out
        assert "measure(body)" in out
        assert "let target-width = size.width * 1" in out
        assert "scale(x: factor, y: factor, reflow: true, body)" in out
        assert "if true {" in out
        assert_snapshot("resize_default", out)

    def test_shrink_only_down(self):
        out = tt(DF).resize(width=0.8, direction="down").render("typst")
        assert "let target-width = size.width * 0.8" in out
        assert "if body-size.width > target-width {" in out
        assert_snapshot("resize_down", out)

    def test_height_target(self):
        out = tt(DF).resize(height=0.5, direction="both").render("typst")
        assert "let target-height = size.height * 0.5" in out
        assert "body-size.height" in out
        assert "target-width" not in out
        assert_snapshot("resize_height", out)

    def test_up_direction(self):
        out = tt(DF).resize(width=0.9, direction="up").render("typst")
        assert "if body-size.width < target-width {" in out

    def test_no_resize_without_direction(self):
        out = tt(DF).render("typst")
        assert "#layout(size => {" not in out

    def test_wraps_rotate_and_align(self):
        t = tt(DF).resize()
        t._typst_opts.rotate_angle = 45
        t._typst_opts.align_figure = "c"
        out = t.render("typst")
        rotate_idx = out.index("#rotate(")
        layout_idx = out.index("#layout(size => {")
        assert layout_idx < rotate_idx

    def test_invalid_direction_raises(self):
        t = tt(DF)
        t._typst_opts.resize_direction = "sideways"
        t._typst_opts.resize_width = 0.5
        with pytest.raises(ValueError, match="resize_direction"):
            t.render("typst")

    def test_invalid_width_raises(self):
        t = tt(DF)
        t._typst_opts.resize_direction = "both"
        t._typst_opts.resize_width = 0
        with pytest.raises(ValueError, match="resize_width"):
            t.render("typst")


@pytest.mark.typst
class TestThemeMultipage:
    def test_enables_scoped_breakable_figure(self):
        out = tt(DF).multipage().render("typst")
        assert '#show figure.where(kind: "tytable"): set block(breakable: true)' in out
        assert "#show figure: set block" not in out
        assert "repeat: true" in out

    def test_can_disable_repeated_headers(self):
        out = tt(DF).multipage(repeat_headers=False).render("typst")
        assert "breakable: true" in out
        assert "repeat: false" in out

    def test_without_figure_uses_breakable_block(self):
        out = tt(DF, figure=False).multipage().render("typst")
        assert out.startswith("#block(breakable: true)[")
        assert "#show figure" not in out

    def test_repeats_complete_grouped_header(self):
        out = tt(DF).group(j={"All columns": [0, 1]}).multipage(repeat_headers=True).render("typst")
        header = out.split("table.header(", 1)[1].split("    ),", 1)[0]
        assert "repeat: true" in header
        assert "All columns" in header
        assert "[A],[B]" in header


@pytest.mark.typst
class TestThemeMethod:
    def test_builtin_method(self):
        t = tt(DF).theme_grid()
        out = t.render("typst")
        assert "(paint: black)" in out
        assert_snapshot("theme_method", out)

    def test_theme_then_user_override(self):
        out = tt(DF).theme_striped().style(i=0, j=0, background="#ff0000").render("typst")
        assert 'rgb("#ff0000")' in out
        assert_snapshot("theme_override", out)

    def test_user_override_is_independent_of_call_order(self):
        before = tt(DF).theme_striped().style(i=0, j=0, background="#ff0000")
        after = tt(DF).style(i=0, j=0, background="#ff0000").theme_striped()
        assert before.render("typst") == after.render("typst")

    def test_later_theme_replaces_earlier_theme(self):
        out = tt(DF).theme_grid().theme_striped().render("typst")
        assert "(paint: black)" not in out
        assert "table.hline" not in out
        assert "#ededed" in out

    def test_can_restore_default_theme(self):
        out = tt(DF).theme_grid().theme_default().render("typst")
        assert "(paint: black)" not in out
        assert out.count("table.hline") == 3

    def test_constructor_rejects_removed_theme_option(self):
        with pytest.raises(TypeError, match="unexpected keyword argument 'theme'"):
            tt(DF, theme="striped")  # type: ignore[call-arg]

    def test_removed_theme_apis_are_absent(self):
        import tytable

        assert not hasattr(tytable, "THEMES")
        assert not hasattr(TyTable, "theme")
        assert not hasattr(TyTable, "theme_empty")
        assert not hasattr(TyTable, "theme_rotate")
        assert not hasattr(TyTable, "theme_resize")
        assert not hasattr(TyTable, "theme_multipage")


@pytest.mark.typst
class TestFootnotes:
    def test_single_unlabelled_note(self):
        out = tt(DF, notes=["Source: Some data"]).render("typst")
        assert "table.footer" in out
        assert "Source: Some data" in out
        assert_snapshot("footnote_single", out)

    def test_multiple_unlabelled_notes(self):
        out = tt(DF, notes=["Note one", "Note two"]).render("typst")
        assert "Note one" in out
        assert "Note two" in out
        assert_snapshot("footnote_multiple", out)

    def test_labelled_note_with_marker(self):
        out = tt(DF, notes=[{"text": "p < 0.05", "marker": "*"}]).render("typst")
        assert "#super[\\*]" in out
        assert_snapshot("footnote_labelled", out)

    def test_targeted_note_marker_in_cell(self):
        df = pl.DataFrame({"A": [10, 20], "B": [30, 40]})
        out = tt(df, notes=[{"text": "Significant", "marker": "*", "i": [0], "j": [0]}]).render(
            "typst"
        )
        assert "#super[\\*]" in out
        assert "Significant" in out
        assert_snapshot("footnote_targeted", out)

    def test_targeted_note_auto_marker(self):
        df = pl.DataFrame({"A": [10, 20], "B": [30, 40]})
        out = tt(df, notes=[{"text": "First note", "i": [0], "j": [0]}]).render("typst")
        assert "#super[1]" in out
        assert_snapshot("footnote_auto_marker", out)

    def test_targeted_note_where_selects_individual_cells(self):
        df = pl.DataFrame({"A": [120, 90], "B": [80, 130]})
        built = build(
            tt(df, notes=[{"text": "Above 100", "where": cs.numeric() > 100}]).theme_plain(),
            "typst",
        )

        assert built.data_body == [
            ["120#super[1]", "80"],
            ["90", "130#super[1]"],
        ]

    def test_targeted_note_where_intersects_i_and_j(self):
        df = pl.DataFrame({"A": [120, 140], "B": [130, 150]})
        built = build(
            tt(
                df,
                notes=[
                    {
                        "text": "Selected high value",
                        "i": 0,
                        "j": "A",
                        "where": cs.numeric() > 100,
                    }
                ],
            ).theme_plain(),
            "typst",
        )

        assert built.data_body == [
            ["120#super[1]", "130"],
            ["140", "150"],
        ]

    def test_targeted_note_regex_selects_columns(self):
        df = pl.DataFrame({"Q1": [10], "Q2": [20], "Total": [30]})
        built = build(
            tt(
                df,
                notes=[{"text": "Quarter", "i": 0, "j": r"^Q", "regex": True}],
            ).theme_plain(),
            "typst",
        )

        assert built.data_body == [["10#super[1]", "20#super[1]", "30"]]

    def test_multiple_targeted_auto_markers(self):
        df = pl.DataFrame({"A": [10, 20], "B": [30, 40]})
        notes = [
            {"text": "First", "i": [0], "j": [0]},
            {"text": "Second", "i": [1], "j": [1]},
        ]
        out = tt(df, notes=notes).render("typst")
        assert "#super[1]" in out
        assert "#super[2]" in out
        assert_snapshot("footnote_auto_multiple", out)

    def test_no_footer_when_no_notes(self):
        out = tt(DF).render("typst")
        assert "table.footer" not in out

    def test_note_object_directly(self):
        from tytable._directives import Note

        t = tt(DF, notes=[Note(text="Direct", marker="x")])
        out = t.render("typst")
        assert "#super[x]" in out
        assert "Direct" in out

    def test_auto_marker_does_not_mutate_frozen_note(self):
        from tytable._directives import Note

        note = Note(text="Direct", i=[0], j=[0])
        table = tt(DF, notes=[note])

        assert note.marker is None
        assert table._notes[0].marker == "1"
        assert table._notes[0] is not note
