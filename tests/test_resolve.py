import polars as pl
import pytest

from tytable._indices import RowLayout, resolve_i, resolve_j, resolve_where


@pytest.fixture
def layout():
    return RowLayout.create(
        source_rows=3,
        column_group_rows=1,
        has_header=True,
        group_body_rows={1},
    )


class TestRowLayout:
    def test_resolved_structure(self, layout):
        assert layout.header_rows == 2
        assert layout.body_rows == 4
        assert layout.total_rows == 6
        assert layout.groupj_rows == (0,)
        assert layout.header_row == 1
        assert layout.groupi_rows == (3,)
        assert layout.data_rows == (2, 4, 5)
        assert layout.first_row == 0
        assert layout.last_row == 5
        assert [layout.kind(row) for row in range(6)] == [
            "groupj",
            "header",
            "data",
            "groupi",
            "data",
            "data",
        ]

    def test_body_mapping(self, layout):
        assert [layout.source_to_display(row) for row in range(3)] == [2, 4, 5]
        assert [layout.body_index(row) for row in range(2, 6)] == [0, 1, 2, 3]

    def test_empty_table_has_no_boundaries(self):
        empty = RowLayout.create(
            source_rows=0,
            column_group_rows=0,
            has_header=False,
            group_body_rows=set(),
        )
        assert empty.first_row is None
        assert empty.last_row is None
        assert empty.total_rows == 0

    def test_header_only_table(self):
        header = RowLayout.create(
            source_rows=0,
            column_group_rows=0,
            has_header=True,
            group_body_rows=set(),
        )
        assert header.header_row == 0
        assert header.first_row == header.last_row == 0

    def test_invalid_group_layout(self):
        with pytest.raises(ValueError, match="valid body layout"):
            RowLayout.create(
                source_rows=1,
                column_group_rows=0,
                has_header=False,
                group_body_rows={3},
            )

    def test_invalid_display_rows(self, layout):
        with pytest.raises(ValueError, match="not a body row"):
            layout.body_index(0)
        with pytest.raises(ValueError, match="outside the table"):
            layout.kind(10)

    def test_supported_row_kinds(self, layout):
        layout.require_supported([1, 2, 3], allowed={"header", "groupi", "data"}, method="x")
        with pytest.raises(ValueError, match=r"x cannot target.*'groupj'"):
            layout.require_supported([0, 2], allowed={"data"}, method="x")


class TestResolveI:
    def test_default_and_named_selectors(self, layout):
        assert resolve_i(None, layout=layout) == [2, 4, 5]
        assert resolve_i("data", layout=layout) == [2, 4, 5]
        assert resolve_i("header", layout=layout) == [1]
        assert resolve_i("groupi", layout=layout) == [3]
        assert resolve_i("groupj", layout=layout) == [0]
        assert resolve_i("all", layout=layout) == [0, 1, 2, 3, 4, 5]

    def test_absent_structural_rows_are_empty(self):
        plain = RowLayout.create(
            source_rows=2,
            column_group_rows=0,
            has_header=False,
            group_body_rows=set(),
        )
        assert resolve_i("header", layout=plain) == []
        assert resolve_i("groupi", layout=plain) == []
        assert resolve_i("groupj", layout=plain) == []

    def test_source_positions_and_mixed_lists(self, layout):
        assert resolve_i(0, layout=layout) == [2]
        assert resolve_i(2, layout=layout) == [5]
        assert resolve_i([2, "header", 0, 2], layout=layout) == [1, 2, 5]
        assert resolve_i([], layout=layout) == []

    @pytest.mark.parametrize("selector", [-1, 3, 10])
    def test_bad_source_position(self, layout, selector):
        with pytest.raises(ValueError):
            resolve_i(selector, layout=layout)

    @pytest.mark.parametrize("selector", [True, [0, True], "bogus", ["bogus"]])
    def test_bad_selector(self, layout, selector):
        with pytest.raises((TypeError, ValueError)):
            resolve_i(selector, layout=layout)


class TestDataDrivenRows:
    DF = pl.DataFrame({"Score": [95, 72, 88], "Grade": ["A", "C", "B"]})

    def test_expression(self, layout):
        assert resolve_i(pl.col("Score") > 80, layout=layout, data=self.DF) == [2, 5]

    def test_boolean_series(self, layout):
        mask = pl.Series([False, True, True])
        assert resolve_i(mask, layout=layout, data=self.DF) == [4, 5]

    def test_boolean_sequence(self, layout):
        assert resolve_i([True, False, True], layout=layout, data=self.DF) == [2, 5]
        assert resolve_i((False, True, False), layout=layout, data=self.DF) == [4]

    def test_callable(self, layout):
        assert resolve_i(lambda row: row["Grade"] == "C", layout=layout, data=self.DF) == [4]

    def test_expression_contracts(self, layout):
        with pytest.raises(ValueError, match="one column"):
            resolve_i(pl.all(), layout=layout, data=self.DF)
        with pytest.raises(TypeError, match="Boolean"):
            resolve_i(pl.col("Score"), layout=layout, data=self.DF)

    def test_series_contracts(self, layout):
        with pytest.raises(TypeError, match="Boolean dtype"):
            resolve_i(pl.Series([1, 2, 3]), layout=layout, data=self.DF)
        with pytest.raises(ValueError, match="length 2"):
            resolve_i(pl.Series([True, False]), layout=layout, data=self.DF)

    def test_boolean_list_contracts(self, layout):
        with pytest.raises(ValueError, match="length 2"):
            resolve_i([True, False], layout=layout, data=self.DF)
        with pytest.raises(TypeError, match="cannot mix"):
            resolve_i([True, 1, False], layout=layout, data=self.DF)
        with pytest.raises(TypeError, match="require source data"):
            resolve_i([True, False, True], layout=layout)


class TestResolveJ:
    COLS = ["A", "B", "name", "value"]

    def test_positions_names_and_lists(self):
        assert resolve_j(None, self.COLS) == [0, 1, 2, 3]
        assert resolve_j(2, self.COLS) == [2]
        assert resolve_j("value", self.COLS) == [3]
        assert resolve_j(["B", 0, "B"], self.COLS) == [0, 1]

    def test_regex(self):
        assert resolve_j("a", self.COLS, regex=True) == [2, 3]
        assert resolve_j(["A", "am"], self.COLS, regex=True) == [0, 2]

    @pytest.mark.parametrize("selector", [-1, 4, True, ["A", True], [object()]])
    def test_invalid_selector(self, selector):
        with pytest.raises((TypeError, ValueError)):
            resolve_j(selector, self.COLS)

    def test_missing_or_invalid_regex(self):
        with pytest.raises(ValueError, match="column not found"):
            resolve_j("missing", self.COLS)
        with pytest.raises(ValueError, match="matched no columns"):
            resolve_j("missing", self.COLS, regex=True)
        with pytest.raises(ValueError, match="invalid regex"):
            resolve_j("[", self.COLS, regex=True)
        with pytest.raises(ValueError, match="maximum 500"):
            resolve_j("a" * 501, self.COLS, regex=True)


class TestResolveWhere:
    DF = pl.DataFrame({"a": [1, 3], "b": [2, 4]})
    LAYOUT = RowLayout.create(
        source_rows=2,
        column_group_rows=0,
        has_header=True,
        group_body_rows={1},
    )

    def test_cells_use_display_coordinates(self):
        assert resolve_where(pl.all() > 2, data=self.DF, layout=self.LAYOUT) == {(3, 0), (3, 1)}

    def test_empty_expression(self):
        assert resolve_where(pl.exclude("a", "b"), data=self.DF, layout=self.LAYOUT) == set()

    def test_contracts(self):
        with pytest.raises(TypeError, match="Polars expression"):
            resolve_where(True, data=self.DF, layout=self.LAYOUT)
        with pytest.raises(TypeError, match="boolean columns"):
            resolve_where(pl.col("a"), data=self.DF, layout=self.LAYOUT)
        with pytest.raises(ValueError, match="do not match source columns"):
            resolve_where((pl.col("a") > 0).alias("unknown"), data=self.DF, layout=self.LAYOUT)
