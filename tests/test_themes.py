import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import THEMES, TinyTable, tt

DF = pl.DataFrame({"A": [1, 3], "B": [2, 4]})


@pytest.mark.typst
class TestThemeDefault:
    def test_booktab_rules(self):
        out = tt(DF, theme="default").render("typst")
        assert out.count("table.hline") == 3
        assert "0.08em" in out
        assert "0.05em" in out
        assert_snapshot("theme_default", out)

    def test_no_colnames_still_top_and_bottom(self):
        df = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
        out = tt(df, theme="default", colnames=False).render("typst")
        assert out.count("table.hline") == 2
        assert_snapshot("theme_default_no_colnames", out)

    def test_with_col_groups(self):
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": [7, 8]})
        out = tt(df, theme="default").group(j={"Group": [0, 1]}).render("typst")
        assert out.count("table.hline") == 3
        assert_snapshot("theme_default_with_groups", out)


@pytest.mark.typst
class TestThemeStriped:
    def test_even_row_background(self):
        out = tt(DF, theme="striped").render("typst")
        assert "#ededed" in out
        assert_snapshot("theme_striped", out)

    def test_three_rows(self):
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        out = tt(df, theme="striped").render("typst")
        assert_snapshot("theme_striped_3rows", out)


@pytest.mark.typst
class TestThemeGrid:
    def test_grid_stroke_and_lines(self):
        out = tt(DF, theme="grid").render("typst")
        assert "(paint: black)" in out
        assert "table.hline" in out
        assert "table.vline" in out
        assert_snapshot("theme_grid", out)


@pytest.mark.typst
class TestThemeEmpty:
    def test_clears_all(self):
        t = tt(DF, theme="default")
        assert len(t._prepare_hooks) > 0
        t.theme("empty")
        assert len(t._style_directives) == 0
        assert len(t._format_directives) == 0
        assert len(t._prepare_hooks) == 0

    def test_no_lines_in_output(self):
        out = tt(DF, theme="empty").render("typst")
        assert "table.hline" not in out
        assert "table.vline" not in out
        assert_snapshot("theme_empty", out)


@pytest.mark.typst
class TestThemeRotate:
    def test_whole_table_rotate(self):
        out = tt(DF, theme="rotate").render("typst")
        assert "#rotate(90" in out
        assert_snapshot("theme_rotate", out)


@pytest.mark.typst
class TestThemeMethod:
    def test_dot_theme(self):
        t = tt(DF, theme=None)
        t.theme("grid")
        out = t.render("typst")
        assert "(paint: black)" in out
        assert_snapshot("theme_method", out)

    def test_callable_theme(self):
        def my_theme(t):
            t.style(i="header", bold=True, background="#333333", color="white")
            return t

        out = tt(DF, theme=None).theme(my_theme).render("typst")
        assert "bold: true" in out
        assert 'background: rgb("#333333")' in out
        assert_snapshot("theme_callable", out)

    def test_theme_then_user_override(self):
        out = tt(DF, theme="striped").style(i=0, j=0, background="#ff0000").render("typst")
        assert 'rgb("#ff0000")' in out
        assert_snapshot("theme_override", out)

    def test_unknown_theme_raises(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            tt(DF, theme="nonexistent")

    def test_theme_none_skips(self):
        t = tt(DF, theme=None)
        assert len(t._style_directives) == 0
        assert len(t._prepare_hooks) == 0

    def test_theme_empty_method(self):
        t = tt(DF)
        t.theme("empty")
        assert len(t._style_directives) == 0


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


@pytest.mark.typst
class TestTHEMES:
    def test_exported(self):
        assert isinstance(THEMES, dict)
        assert "default" in THEMES
        assert THEMES["default"] is not None
        assert callable(THEMES["default"])

    def test_theme_returns_table(self):
        t = tt(DF, theme=None)
        result = THEMES["default"](t)
        assert isinstance(result, TinyTable)
        assert result is t
