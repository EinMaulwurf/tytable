import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._indices import resolve_j


@pytest.mark.typst
class TestSetNamePerColumn:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_rename_by_name_updates_colnames(self):
        t = tt(self.DF, theme=None)
        assert t.set_name(j="x", name="X") is t
        assert t._colnames == ["X", "y"]

    def test_rename_by_int_position(self):
        t = tt(self.DF, theme=None)
        t.set_name(j=0, name="Alpha")
        assert t._colnames == ["Alpha", "y"]

    def test_rename_by_list_of_names(self):
        t = tt(self.DF, theme=None)
        t.set_name(j=["x", "y"], name=["X", "Y"])
        assert t._colnames == ["X", "Y"]

    def test_rename_by_list_of_ints(self):
        t = tt(self.DF, theme=None)
        t.set_name(j=[0, 1], name=["X", "Y"])
        assert t._colnames == ["X", "Y"]

    def test_rename_by_regex(self):
        df = pl.DataFrame({"col_a": [1], "col_b": [2], "other": [3]})
        t = tt(df, theme=None)
        t.set_name(j="col_", name="matched")
        assert t._colnames == ["matched", "matched", "other"]

    def test_single_str_applies_to_all_matched(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        t = tt(df, theme=None)
        t.set_name(j=["a", "b"], name="")
        assert t._colnames == ["", ""]

    def test_render_shows_new_header(self):
        out = tt(self.DF, theme=None).set_name(j="x", name="X").render("typst")
        assert "[X],[y]," in out
        assert "[x],[y]," not in out

    def test_chaining_returns_self(self):
        t = tt(self.DF, theme=None)
        assert t.set_name(j="x", name="X") is t


@pytest.mark.typst
class TestSetNameFullList:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_replace_all_names(self):
        t = tt(self.DF, theme=None)
        assert t.set_name(name=["Alpha", "Beta"]) is t
        assert t._colnames == ["Alpha", "Beta"]

    def test_replace_all_renders_new_headers(self):
        out = tt(self.DF, theme=None).set_name(name=["Alpha", "Beta"]).render("typst")
        assert "[Alpha],[Beta]," in out

    def test_replace_all_wrong_length_raises(self):
        t = tt(self.DF, theme=None)
        with pytest.raises(ValueError, match="1 name\\(s\\) for a 2-column table"):
            t.set_name(name=["only_one"])
        with pytest.raises(ValueError, match="3 name\\(s\\) for a 2-column table"):
            t.set_name(name=["a", "b", "c"])

    def test_single_str_with_j_none_raises(self):
        t = tt(self.DF, theme=None)
        with pytest.raises(ValueError, match="requires a column selector j"):
            t.set_name(name="Only")


@pytest.mark.typst
class TestSetNameEdgeCases:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_empty_string_name_renders_empty_cell(self):
        out = tt(self.DF, theme=None).set_name(j="x", name="").render("typst")
        assert "[],[y]," in out

    def test_empty_string_full_list(self):
        out = (
            tt(self.DF, theme=None)
            .set_name(name=["", ""])
            .render("typst")
        )
        assert "[],[]," in out

    def test_original_dataframe_untouched(self):
        df = self.DF
        t = tt(df, theme=None).set_name(j="x", name="X")
        assert df.columns == ["x", "y"]
        assert t._data.columns == ["x", "y"]
        assert t._colnames == ["X", "y"]

    def test_per_column_list_length_mismatch_raises(self):
        t = tt(self.DF, theme=None)
        with pytest.raises(ValueError, match="1 name\\(s\\) for 2 selected column\\(s\\)"):
            t.set_name(j=["x", "y"], name=["only_one"])

    def test_selector_matches_nothing_raises(self):
        t = tt(self.DF, theme=None)
        with pytest.raises(ValueError, match="matched no columns"):
            t.set_name(j="zzz", name="X")

    def test_duplicate_display_names_allowed(self):
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        t = tt(df, theme=None).set_name(name=["", "", ""])
        assert t._colnames == ["", "", ""]
        out = t.render("typst")
        assert out.count("[],") >= 3


@pytest.mark.typst
class TestSetNameSelectorSemantics:
    """After renaming, subsequent j selectors use the NEW display name."""

    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_style_uses_new_name(self):
        out = (
            tt(self.DF, theme=None)
            .set_name(j="x", name="X")
            .style(j="X", bold=True)
            .render("typst")
        )
        assert_snapshot("set_name_style_new_name", out)

    def test_old_name_no_longer_matches(self):
        t = tt(self.DF, theme=None).set_name(j="x", name="X")
        assert resolve_j("x", t._colnames) == []
        assert resolve_j("X", t._colnames) == [1]

    def test_old_name_in_style_silently_noops(self):
        """j='x' after rename is a no-op regex (no error, no style applied)."""
        out_a = (
            tt(self.DF, theme=None)
            .set_name(j="x", name="X")
            .style(j="x", bold=True)
            .render("typst")
        )
        out_b = tt(self.DF, theme=None).set_name(j="x", name="X").render("typst")
        assert out_a == out_b

    def test_rename_then_group_uses_new_name(self):
        df = pl.DataFrame({"Q1_rev": [1], "Q1_cost": [2]})
        t = tt(df, theme=None).set_name(name=["rev", "cost"])
        t.group(j={"Q1": ["rev", "cost"]})
        out = t.render("typst")
        assert_snapshot("set_name_then_group", out)

    def test_rename_then_fmt_uses_new_name(self):
        df = pl.DataFrame({"x": [1.5, 2.5]})
        out = (
            tt(df, theme=None)
            .set_name(j="x", name="Value")
            .fmt(j="Value", digits=2)
            .render("typst")
        )
        assert "[1.50]" in out
        assert "[2.50]" in out


@pytest.mark.typst
class TestSetNameSnapshots:
    def test_snapshot_per_column_rename(self):
        df = pl.DataFrame({"x": [1, 3], "y": [2, 4]})
        out = (
            tt(df, theme=None)
            .set_name(j="x", name="Variable")
            .set_name(j="y", name="Value")
            .render("typst")
        )
        assert_snapshot("set_name_per_column", out)

    def test_snapshot_full_list_with_empty(self):
        df = pl.DataFrame({"name": ["alice"], "score": [42]})
        out = (
            tt(df, theme=None)
            .set_name(name=["", "Score"])
            .render("typst")
        )
        assert_snapshot("set_name_full_list_empty", out)


@pytest.mark.html
class TestSetNameHtml:
    def test_html_rename_header(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        out = tt(df, theme=None).set_name(j="x", name="Renamed").render("html")
        assert "<th>Renamed</th>" in out


@pytest.mark.typst
class TestSetNameColnamesOverrideInterplay:
    def test_set_name_after_override_renames_further(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df, theme=None, colnames_override={"x": "X1", "y": "Y1"})
        assert t._colnames == ["X1", "Y1"]
        t.set_name(j="X1", name="X2")
        assert t._colnames == ["X2", "Y1"]

    def test_set_name_full_list_overrides_override(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df, theme=None, colnames_override={"x": "X1", "y": "Y1"})
        t.set_name(name=["A", "B"])
        assert t._colnames == ["A", "B"]
