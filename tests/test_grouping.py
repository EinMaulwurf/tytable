import polars as pl
import polars.selectors as cs
import pytest

from tests.helpers import assert_snapshot
from tytable import groupj, tt
from tytable._groups import _resolve_col_group_spans
from tytable._resolve import build
from tytable._styling import resolve_line_edges

DF = pl.DataFrame({"A": [1, 3], "B": [2, 4]})
DF3 = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9], "d": [10, 11, 12]})
DF4 = pl.DataFrame({"Q1_a": [1, 2], "Q1_b": [3, 4], "Q2_c": [5, 6], "Q2_d": [7, 8]})


def test_resolve_col_group_spans():
    row = ["Group", "", None, "Solo", "", ""]
    assert _resolve_col_group_spans(row) == [
        ("Group", 0, 2),
        ("", 2, 1),
        ("Solo", 3, 3),
    ]


@pytest.mark.typst
class TestRowGroups:
    def test_single_row_group(self):
        out = tt(DF).group(i={"My Group": 0}).render("typst")
        assert "table.cell(colspan: 2)[My Group]" in out
        assert_snapshot("group_row_single", out)

    def test_multiple_row_groups(self):
        df = pl.DataFrame({"a": [1, 2, 3, 4, 5], "b": [6, 7, 8, 9, 10]})
        out = tt(df).group(i={"First": 0, "Second": 2}).render("typst")
        assert "table.cell(colspan: 2)[First]" in out
        assert "table.cell(colspan: 2)[Second]" in out
        assert_snapshot("group_row_multiple", out)

    def test_row_group_at_end(self):
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        out = tt(df).group(i={"End": 1}).render("typst")
        assert "table.cell(colspan: 2)[End]" in out
        assert_snapshot("group_row_end", out)

    def test_row_group_at_position_zero(self):
        out = tt(DF).group(i={"Start": 0}).render("typst")
        assert "table.header" in out
        assert "table.cell(colspan: 2)[Start]" in out

    def test_row_groups_from_run_length_list(self):
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5]})
        built = build(tt(df).theme_plain().group(i=["A", "A", "B", "B", "C"]), "typst")
        assert built.layout.groupi_rows == (1, 4, 7)
        assert [row[0] for row in built.data_body] == ["A", "1", "2", "B", "3", "4", "C", "5"]

    def test_row_groups_from_run_length_tuple(self):
        built = build(tt(DF).theme_plain().group(i=("A", "B")), "typst")
        assert built.layout.groupi_rows == (1, 3)
        assert [row[0] for row in built.data_body] == ["A", "1", "B", "3"]


@pytest.mark.typst
class TestRowGroupPositionFormula:
    def test_position_shift(self):
        df = pl.DataFrame({"a": [1, 2, 3, 4, 5], "b": [6, 7, 8, 9, 10]})
        built = build(tt(df).group(i={"G1": 1, "G2": 3}), "typst")
        assert built.layout.header_rows == 1
        assert len(built.data_body) == 7
        assert built.data_body[1][0] == "G1"
        assert built.data_body[4][0] == "G2"


@pytest.mark.typst
class TestColumnGroups:
    def test_single_column_group(self):
        out = tt(DF3).group(j={"Group": [0, 1]}).render("typst")
        assert "table.cell(colspan: 2, align: center)[Group]" in out
        assert "[c]," in out
        assert "[d]," in out
        assert_snapshot("group_col_single", out)

    def test_multiple_column_groups_same_row(self):
        out = tt(DF3).group(j={"G1": [0, 1], "G2": [2, 3]}).render("typst")
        assert "table.cell(colspan: 2, align: center)[G1]" in out
        assert "table.cell(colspan: 2, align: center)[G2]" in out
        assert_snapshot("group_col_multiple_same_row", out)

    def test_stacked_column_groups(self):
        out = tt(DF4).group(j={"Region": [0, 1], "City": [2, 3]}).render("typst")
        assert "Region" in out
        assert "City" in out
        assert_snapshot("group_col_stacked_basic", out)

    def test_column_group_by_name(self):
        out = tt(DF3).group(j={"G": ["a", "b"]}).render("typst")
        assert "table.cell(colspan: 2, align: center)[G]" in out
        assert "[c]," in out
        assert_snapshot("group_col_by_name", out)

    def test_column_group_from_tuple(self):
        out = tt(DF3).group(j={"Group": (0, 1)}).render("typst")
        assert "table.cell(colspan: 2, align: center)[Group]" in out

    def test_column_group_ungrouped_columns(self):
        out = tt(DF3).group(j={"G": [0, 1]}).render("typst")
        assert "[ ]" in out
        assert_snapshot("group_col_ungrouped", out)

    def test_single_column_group_no_colspan(self):
        out = tt(DF).group(j={"Only": [0]}).render("typst")
        assert "table.cell(align: center)[Only]" in out
        assert "table.cell(colspan:" not in out
        assert "[Only]" in out

    def test_nested_group_levels_are_numbered_from_innermost(self):
        table = (
            tt(DF3)
            .theme_plain()
            .group(j={"Inner left": ["a", "b"], "Inner right": ["c", "d"]})
            .group(j={"Outer": ["a", "b", "c", "d"]})
            .style(i=groupj(level=0), j="b", color="blue")
            .style(i=groupj(level=0), j="c", color="red")
            .style(i=groupj(level=1), bold=True)
        )

        built = build(table, "html")

        assert built.layout.groupj_levels == (1, 0)
        assert built.style_grid[(0, 0)]["bold"] is True
        assert built.style_grid[(1, 0)]["color"] == "blue"
        assert built.style_grid[(1, 2)]["color"] == "red"
        assert "color:#0000ff" in table.render("html")
        assert "color:#ff0000" in table.render("html")

    def test_groupj_string_selects_every_covering_group_cell(self):
        built = build(
            tt(DF3)
            .theme_plain()
            .group(j={"Inner": ["a", "b"]})
            .group(j={"Outer": ["a", "b", "c"]})
            .style(i="groupj", j="b", italic=True),
            "typst",
        )

        assert built.style_grid[(0, 0)]["italic"] is True
        assert built.style_grid[(1, 0)]["italic"] is True

    def test_groupj_member_columns_deduplicate_to_the_spanning_cell(self):
        built = build(
            tt(DF3)
            .theme_plain()
            .group(j={"Group": ["a", "b"]})
            .style(i=groupj(level=0), j=["a", "b"], background="#eeeeee"),
            "html",
        )

        assert built.style_grid[(0, 0)]["background"] == "#eeeeee"
        assert (0, 1) not in built.style_grid

    def test_groupj_rejects_conflicting_alignment_for_one_spanning_cell(self):
        table = (
            tt(DF3)
            .group(j={"Group": ["a", "b"]})
            .style(i=groupj(level=0), j=["a", "b"], align="lr")
        )

        with pytest.raises(ValueError, match="conflicting values"):
            table.render("html")

    def test_groupj_border_covers_the_complete_spanning_cell(self):
        built = build(
            tt(DF3)
            .theme_plain()
            .group(j={"Group": ["a", "b"]})
            .style(i=groupj(level=0), j="b", line="tblr", line_color="blue"),
            "typst",
        )

        edges = resolve_line_edges(built.style_lines)
        assert {key for key in edges if key[0] == "h"} == {
            ("h", 0, 0),
            ("h", 0, 1),
            ("h", 1, 0),
            ("h", 1, 1),
        }
        assert ("v", 0, 0) in edges
        assert ("v", 2, 0) in edges

    def test_groupj_levels_keep_their_identity_when_projection_removes_a_level(self):
        table = (
            tt(DF3)
            .theme_plain()
            .group(j={"Inner": ["a", "b"]})
            .group(j={"Outer": ["c", "d"]})
            .style(i=groupj(level=0), bold=True)
            .style(i=groupj(level=1), italic=True)
            .show_columns(["a", "b"])
        )

        built = build(table, "typst")

        assert built.layout.groupj_levels == (0,)
        assert built.layout.column_group_levels == 2
        assert built.style_grid[(0, 0)]["bold"] is True
        assert all("italic" not in props for props in built.style_grid.values())

    def test_groupj_style_on_a_hidden_member_does_not_target_the_surviving_group(self):
        built = build(
            tt(DF3)
            .theme_plain()
            .group(j={"Group": ["a", "b"]})
            .style(i=groupj(level=0), j="b", color="blue")
            .show_columns("a"),
            "html",
        )

        assert all("color" not in props for props in built.style_grid.values())


@pytest.mark.typst
class TestHeaderRows:
    def test_no_groups(self):
        built = build(tt(DF), "typst")
        assert built.layout.header_rows == 1

    def test_one_col_group(self):
        built = build(tt(DF).group(j={"G": [0, 1]}), "typst")
        assert built.layout.header_rows == 2

    def test_two_col_groups(self):
        built = build(tt(DF).group(j={"G": [0, 1]}).group(j={"T": [0, 1]}), "typst")
        assert built.layout.header_rows == 3

    def test_no_colnames_with_col_groups(self):
        built = build(tt(DF, colnames=False).group(j={"G": [0, 1]}), "typst")
        assert built.layout.header_rows == 1

    def test_no_colnames_no_groups(self):
        built = build(tt(DF, colnames=False), "typst")
        assert built.layout.header_rows == 0

    def test_groupj_hits_every_column_group_level(self):
        built = build(
            tt(DF)
            .group(j={"Bottom": [0, 1]})
            .group(j={"Top": [0, 1]})
            .style(i="groupj", bold=True),
            "typst",
        )
        assert built.style_grid[(0, 0)].get("bold") is True
        assert built.style_grid[(1, 0)].get("bold") is True


@pytest.mark.typst
class TestCombinedGroups:
    def test_row_and_col_groups(self):
        df = pl.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
        out = tt(df).group(j={"H": [0, 1]}).group(i={"G": 2}).render("typst")
        assert "table.cell(colspan: 2, align: center)[H]" in out
        assert "table.cell(colspan: 2)[G]" in out
        assert_snapshot("group_combined", out)

    def test_row_group_after_col_group_stacks(self):
        df = pl.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
        built = build(
            tt(df).group(j={"H": [0, 1]}).group(i={"G": 2}).style(i="groupi", bold=True),
            "typst",
        )
        assert built.layout.groupi_rows == (4,)
        assert built.style_grid[(4, 0)].get("bold") is True


@pytest.mark.typst
class TestGroupiStyling:
    def test_groupi_bold(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        out = tt(df).group(i={"G": 1}).style(i="groupi", bold=True).render("typst")
        assert "(bold: true,)" in out
        assert_snapshot("group_groupi_bold", out)

    def test_groupi_background(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        out = tt(df).group(i={"G": 1}).style(i="groupi", background="#f0f0f0").render("typst")
        assert 'background: rgb("#f0f0f0")' in out
        assert_snapshot("group_groupi_background", out)


@pytest.mark.typst
class TestGroupValidation:
    def test_invalid_row_group_type(self):
        with pytest.raises(TypeError):
            tt(DF).group(i="invalid")

    def test_invalid_col_group_type(self):
        with pytest.raises(TypeError):
            tt(DF).group(j=123)

    def test_string_is_not_a_col_group_spec(self):
        with pytest.raises(TypeError, match=r"group\(j=.*must be a mapping"):
            tt(DF4).group(j="_")

    def test_j_and_delimiter_are_mutually_exclusive(self):
        with pytest.raises(ValueError, match="either j or delimiter"):
            tt(DF4).group(j={"Q1": [0, 1]}, delimiter="_")

    @pytest.mark.parametrize("groups", [["A"], ["A", "A", "B"]])
    def test_row_group_list_must_match_data_rows(self, groups):
        with pytest.raises(ValueError, match="exactly 2 entries"):
            tt(DF).group(i=groups)

    @pytest.mark.parametrize("groups", [{"Low": -1}, {"High": 3}])
    def test_row_group_position_must_be_in_range(self, groups):
        with pytest.raises(IndexError, match="out of range for 2 rows"):
            tt(DF).group(i=groups)

    @pytest.mark.parametrize("position", [True, 1.5, "1"])
    def test_row_group_position_must_be_an_integer(self, position):
        with pytest.raises(TypeError, match="must be an integer"):
            tt(DF).group(i={"Group": position})

    def test_row_groups_cannot_share_a_position(self):
        with pytest.raises(ValueError, match="multiple row groups"):
            tt(DF).group(i={"First": 1, "Second": 1})

    @pytest.mark.parametrize("groups", [{None: 0}, ["A", None]])
    def test_row_group_labels_must_not_be_none(self, groups):
        with pytest.raises(ValueError, match="labels must not be None"):
            tt(DF).group(i=groups)

    def test_empty_row_group_specs_are_noops(self):
        table = tt(pl.DataFrame({"A": []})).group(i=[]).group(i={})
        assert table._row_groups == []

    @pytest.mark.parametrize("position", [-1, 4])
    def test_column_group_position_must_be_in_range(self, position):
        with pytest.raises(IndexError, match="out of range for 4 columns"):
            tt(DF3).group(j={"Group": [position]})

    def test_boolean_is_not_a_column_position(self):
        with pytest.raises(TypeError, match="got bool"):
            tt(DF3).group(j={"Group": [True]})

    @pytest.mark.parametrize("columns", [[0, 0], [0, 2], [2, 1]])
    def test_column_group_columns_must_be_unique_contiguous_and_ordered(self, columns):
        with pytest.raises(ValueError, match="duplicate|contiguous"):
            tt(DF3).group(j={"Group": columns})

    def test_column_groups_must_not_overlap(self):
        with pytest.raises(ValueError, match="overlaps another group"):
            tt(DF3).group(j={"First": [0, 1], "Second": [1, 2]})

    def test_column_group_must_not_be_empty(self):
        with pytest.raises(ValueError, match="at least one column"):
            tt(DF3).group(j={"Group": []})

    def test_column_group_columns_must_be_a_sequence(self):
        with pytest.raises(TypeError, match="must be a sequence"):
            tt(DF3).group(j={"Group": "ab"})

    def test_column_group_label_must_not_be_none(self):
        with pytest.raises(ValueError, match="labels must not be None"):
            tt(DF3).group(j={None: [0, 1]})

    def test_empty_column_group_spec_is_a_noop(self):
        built = build(tt(DF).group(j={}), "typst")
        assert built.col_groups == []
        assert built.layout.header_rows == 1

    def test_column_group_accepts_polars_selector(self):
        df = pl.DataFrame({"label": ["a"], "q1": [1], "q2": [2.0]})
        built = build(tt(df).group(j={"Measures": cs.numeric()}), "typst")
        assert built.col_groups == [[None, "Measures", ""]]

    def test_column_group_selector_must_be_contiguous(self):
        df = pl.DataFrame({"q1": [1], "label": ["a"], "q2": [2.0]})
        with pytest.raises(ValueError, match="contiguous"):
            tt(df).group(j={"Measures": cs.numeric()})

    def test_empty_column_group_selector_is_rejected(self):
        with pytest.raises(ValueError, match="at least one column"):
            tt(DF).group(j={"Missing": cs.starts_with("missing")})


@pytest.mark.typst
class TestDelimiterGrouping:
    def test_delimiter_single_level(self):
        out = tt(DF4).group(delimiter="_").render("typst")
        assert_snapshot("group_delim", out)

    def test_delimiter_levels_are_numbered_from_innermost(self):
        built = build(
            tt(DF4)
            .theme_plain()
            .group(delimiter="_")
            .style(i=groupj(level=0), j="Q1_b", color="blue")
            .style(i=groupj(level=1), j="Q1_b", bold=True),
            "typst",
        )

        assert built.layout.groupj_levels == (1, 0)
        assert built.style_grid[(0, 0)]["bold"] is True
        assert built.style_grid[(1, 1)]["color"] == "blue"

    def test_delimiter_uses_source_names_after_display_rename(self):
        built = build(
            tt(DF4).set_name(name=["One", "Two", "Three", "Four"]).group(delimiter="_"),
            "typst",
        )
        assert built.col_groups[0][0] == "Q1"
        assert built.colnames_display == ["One", "Two", "Three", "Four"]

    def test_delimiter_mismatched_parts(self):
        df = pl.DataFrame({"A_b": [1], "C": [2]})
        with pytest.raises(ValueError):
            tt(df).group(delimiter="_")

    def test_delimiter_basic(self):
        df = pl.DataFrame({"A_x": [1], "A_y": [2]})
        out = tt(df).group(delimiter="_")
        result = out.render("typst")
        assert "table.header" in result

    def test_delimiter_must_not_be_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            tt(DF).group(delimiter="")

    def test_delimiter_must_occur_in_every_column(self):
        with pytest.raises(ValueError, match="must occur in every column name"):
            tt(DF).group(delimiter="_")
