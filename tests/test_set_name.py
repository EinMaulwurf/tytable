import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._resolve import build


@pytest.mark.typst
class TestSetNamePerColumn:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_rename_by_name_updates_colnames(self):
        t = tt(self.DF).theme_plain()
        assert t.set_name(j="x", name="X") is t
        assert t._colnames_display == ["X", "y"]
        assert t._source_colnames == ["x", "y"]

    def test_rename_by_int_position(self):
        t = tt(self.DF).theme_plain()
        t.set_name(j=0, name="Alpha")
        assert t._colnames_display == ["Alpha", "y"]

    def test_rename_by_list_of_names(self):
        t = tt(self.DF).theme_plain()
        t.set_name(j=["x", "y"], name=["X", "Y"])
        assert t._colnames_display == ["X", "Y"]

    def test_rename_by_list_of_ints(self):
        t = tt(self.DF).theme_plain()
        t.set_name(j=[0, 1], name=["X", "Y"])
        assert t._colnames_display == ["X", "Y"]

    def test_rename_by_regex(self):
        df = pl.DataFrame({"col_a": [1], "col_b": [2], "other": [3]})
        t = tt(df).theme_plain()
        t.set_name(j="col_", regex=True, name="matched")
        assert t._colnames_display == ["matched", "matched", "other"]

    def test_single_str_applies_to_all_matched(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        t = tt(df).theme_plain()
        t.set_name(j=["a", "b"], name="")
        assert t._colnames_display == ["", ""]

    def test_render_shows_new_header(self):
        out = tt(self.DF).theme_plain().set_name(j="x", name="X").render("typst")
        assert "[X],[y]," in out
        assert "[x],[y]," not in out

    def test_chaining_returns_self(self):
        t = tt(self.DF).theme_plain()
        assert t.set_name(j="x", name="X") is t


@pytest.mark.typst
class TestSetNameFullList:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_replace_all_names(self):
        t = tt(self.DF).theme_plain()
        assert t.set_name(name=["Alpha", "Beta"]) is t
        assert t._colnames_display == ["Alpha", "Beta"]

    def test_replace_all_renders_new_headers(self):
        out = tt(self.DF).theme_plain().set_name(name=["Alpha", "Beta"]).render("typst")
        assert "[Alpha],[Beta]," in out

    def test_replace_all_wrong_length_raises(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(ValueError, match="1 name\\(s\\) for a 2-column table"):
            t.set_name(name=["only_one"])
        with pytest.raises(ValueError, match="3 name\\(s\\) for a 2-column table"):
            t.set_name(name=["a", "b", "c"])

    def test_single_str_with_j_none_raises(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(ValueError, match="requires a column selector j"):
            t.set_name(name="Only")

    def test_non_string_scalar_name_raises_clear_error(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(
            TypeError, match="name must be a string, sequence of strings, or mapping"
        ):
            t.set_name(j="x", name=123)  # type: ignore[arg-type]

    def test_name_sequence_rejects_non_strings(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(TypeError, match="sequence must contain only strings"):
            t.set_name(name=["X", 123])  # type: ignore[list-item]


@pytest.mark.typst
class TestSetNameEdgeCases:
    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_empty_string_name_renders_empty_cell(self):
        out = tt(self.DF).theme_plain().set_name(j="x", name="").render("typst")
        assert "[],[y]," in out

    def test_empty_string_full_list(self):
        out = tt(self.DF).theme_plain().set_name(name=["", ""]).render("typst")
        assert "[],[]," in out

    def test_original_dataframe_untouched(self):
        df = self.DF
        t = tt(df).theme_plain().set_name(j="x", name="X")
        assert df.columns == ["x", "y"]
        assert t._data.columns == ["x", "y"]
        assert t._colnames_display == ["X", "y"]

    def test_per_column_list_length_mismatch_raises(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(ValueError, match="1 name\\(s\\) for 2 selected column\\(s\\)"):
            t.set_name(j=["x", "y"], name=["only_one"])

    def test_selector_matches_nothing_raises(self):
        t = tt(self.DF).theme_plain()
        with pytest.raises(ValueError, match="column not found"):
            t.set_name(j="zzz", name="X")

    def test_duplicate_display_names_allowed(self):
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        t = tt(df).theme_plain().set_name(name=["", "", ""])
        assert t._colnames_display == ["", "", ""]
        out = t.render("typst")
        assert out.count("[],") >= 3


@pytest.mark.typst
class TestSetNameSelectorSemantics:
    """Display renames never alter stable source-name selectors."""

    DF = pl.DataFrame({"x": [1, 3], "y": [2, 4]})

    def test_style_is_order_independent(self):
        before = build(
            tt(self.DF).theme_plain().style(j="x", bold=True).set_name(j="x", name="X"),
            "typst",
        )
        after = build(
            tt(self.DF).theme_plain().set_name(j="x", name="X").style(j="x", bold=True),
            "typst",
        )
        assert before.style_grid == after.style_grid
        assert before.style_grid[(1, 0)]["bold"] is True
        assert (1, 2) not in before.style_grid

    def test_display_name_is_not_a_selector(self):
        t = tt(self.DF).theme_plain().set_name(j="x", name="X").style(j="X", bold=True)
        with pytest.raises(ValueError, match="column not found: 'X'"):
            t.render("typst")

    def test_rename_then_group_uses_source_name(self):
        df = pl.DataFrame({"Q1_rev": [1], "Q1_cost": [2]})
        t = tt(df).theme_plain().set_name(name=["rev", "cost"])
        t.group(j={"Q1": ["Q1_rev", "Q1_cost"]})
        out = t.render("typst")
        assert_snapshot("set_name_then_group", out)

    def test_duplicate_display_names_do_not_make_fmt_ambiguous(self):
        df = pl.DataFrame({"revenue": [1.5], "cost": [2.5]})
        built = build(
            tt(df)
            .theme_plain()
            .set_name(j="revenue", name="Value")
            .set_name(j="cost", name="Value")
            .fmt(j="revenue", digits=2),
            "typst",
        )
        assert built.colnames_display == ["Value", "Value"]
        assert built.data_body == [["1.50", "2.5"]]

    def test_regex_searches_source_names_after_rename(self):
        df = pl.DataFrame({"revenue_q1": [1], "cost_q1": [2]})
        built = build(
            tt(df).theme_plain().set_name(name=["", ""]).style(j="^revenue", regex=True, bold=True),
            "typst",
        )
        assert built.style_grid[(1, 0)]["bold"] is True
        assert (1, 2) not in built.style_grid

    def test_notes_use_source_names_with_duplicate_labels(self):
        df = pl.DataFrame({"revenue": [1], "cost": [2]})
        built = build(
            tt(
                df,
                notes=[{"text": "Revenue note", "i": [0], "j": ["revenue"]}],
            )
            .theme_plain()
            .set_name(name=["Value", "Value"]),
            "typst",
        )
        assert "#super[1]" in built.data_body[0][0]
        assert "#super[1]" not in built.data_body[0][1]

    def test_set_name_selector_remains_a_source_name(self):
        t = tt(self.DF).set_name(j="x", name="X").set_name(j="x", name="Again")
        assert t._colnames_display == ["Again", "y"]
        with pytest.raises(ValueError, match="column not found: 'Again'"):
            t.set_name(j="Again", name="Nope")

    def test_display_label_collision_selects_the_source_column(self):
        df = pl.DataFrame({"a": [1], "Value": [2]})
        t = tt(df).set_name(j="a", name="Value").set_name(j="Value", name="Second")

        assert t._colnames_display == ["Value", "Second"]

    def test_static_images_use_source_names_after_rename(self):
        df = pl.DataFrame({"revenue": [1], "cost": [2]})
        built = build(
            tt(df)
            .theme_plain()
            .set_name(name=["Value", "Value"])
            .images(j="revenue", paths=["revenue.png"]),
            "typst",
        )
        assert "revenue.png" in built.data_body[0][0]
        assert built.data_body[0][1] == "2"

    def test_integer_selector_still_uses_source_position(self):
        built = build(
            tt(self.DF).theme_plain().set_name(name=["", ""]).style(j=1, bold=True),
            "typst",
        )
        assert built.style_grid[(1, 1)]["bold"] is True
        assert (1, 0) not in built.style_grid


@pytest.mark.typst
class TestSetNameSnapshots:
    def test_snapshot_per_column_rename(self):
        df = pl.DataFrame({"x": [1, 3], "y": [2, 4]})
        out = (
            tt(df)
            .theme_plain()
            .set_name(j="x", name="Variable")
            .set_name(j="y", name="Value")
            .render("typst")
        )
        assert_snapshot("set_name_per_column", out)

    def test_snapshot_full_list_with_empty(self):
        df = pl.DataFrame({"name": ["alice"], "score": [42]})
        out = tt(df).theme_plain().set_name(name=["", "Score"]).render("typst")
        assert_snapshot("set_name_full_list_empty", out)


@pytest.mark.html
class TestSetNameHtml:
    def test_html_rename_header(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        out = tt(df).theme_plain().set_name(j="x", name="Renamed").render("html")
        assert '<th style="text-align:right">Renamed</th>' in out


@pytest.mark.typst
class TestSetNameMapping:
    def test_partial_mapping_renames_display_headers(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df).theme_plain().set_name(name={"x": "X"})
        assert t._colnames_display == ["X", "y"]
        assert "[X],[y]," in t.render("typst")

    def test_mapping_returns_self(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df).theme_plain()
        assert t.set_name(name={"x": "X", "y": "Y"}) is t

    def test_mapping_display_names_are_not_selectors(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df).theme_plain().set_name(name={"x": "X"}).style(j="X", bold=True)
        with pytest.raises(ValueError, match="column not found: 'X'"):
            t.render("typst")

    def test_mapping_rejects_unknown_source_without_partial_update(self):
        df = pl.DataFrame({"x": [1], "y": [2]})
        t = tt(df).theme_plain()
        with pytest.raises(ValueError, match="column not found: 'missing'"):
            t.set_name(name={"x": "X", "missing": "Missing"})
        assert t._colnames_display == ["x", "y"]

    @pytest.mark.parametrize("name", [{1: "X"}, {"x": 1}])
    def test_mapping_rejects_non_string_keys_or_values(self, name):
        t = tt(pl.DataFrame({"x": [1]})).theme_plain()
        with pytest.raises(TypeError, match="only string keys and values"):
            t.set_name(name=name)

    def test_mapping_rejects_j(self):
        t = tt(pl.DataFrame({"x": [1]})).theme_plain()
        with pytest.raises(ValueError, match="cannot be combined with j"):
            t.set_name(j="x", name={"x": "X"})

    def test_mapping_rejects_regex(self):
        t = tt(pl.DataFrame({"x": [1]})).theme_plain()
        with pytest.raises(ValueError, match="cannot be combined with regex=True"):
            t.set_name(regex=True, name={"x": "X"})
