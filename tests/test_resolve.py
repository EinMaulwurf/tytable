import polars as pl
import pytest

from tytable._indices import _map_original_to_internal, resolve_i, resolve_j


class TestResolveI:
    def test_none_selects_data(self):
        assert resolve_i(None, nhead=1, group_positions={2}, n_merged_body=4, has_header=True) == [
            1,
            3,
            4,
        ]

    def test_header(self):
        assert resolve_i(
            "header", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [0]
        assert (
            resolve_i("header", nhead=0, group_positions=set(), n_merged_body=3, has_header=False)
            == []
        )

    def test_data(self):
        assert resolve_i(
            "data", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [1, 2, 3]

    def test_all(self):
        assert resolve_i(
            "all", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [0, 1, 2, 3]

    def test_groupi_empty(self):
        assert (
            resolve_i("groupi", nhead=1, group_positions=set(), n_merged_body=3, has_header=True)
            == []
        )

    def test_groupj_empty(self):
        assert (
            resolve_i("groupj", nhead=1, group_positions=set(), n_merged_body=3, has_header=True)
            == []
        )

    def test_groupi_with_positions(self):
        assert resolve_i(
            "groupi", nhead=1, group_positions={2, 5}, n_merged_body=6, has_header=True
        ) == [2, 5]
        assert resolve_i(
            "data", nhead=1, group_positions={2}, n_merged_body=4, has_header=True
        ) == [1, 3, 4]

    def test_numeric(self):
        assert resolve_i(0, nhead=1, group_positions=set(), n_merged_body=3, has_header=True) == [1]
        assert resolve_i(2, nhead=1, group_positions=set(), n_merged_body=3, has_header=True) == [3]

    def test_numeric_list(self):
        assert resolve_i(
            [0, 1, 2], nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [1, 2, 3]

    def test_numeric_maps_source_rows_past_groups(self):
        assert resolve_i(
            [2, 0, 2],
            nhead=1,
            group_positions={1, 3, 6},
            n_merged_body=6,
            has_header=True,
        ) == [2, 5]

    @pytest.mark.parametrize("selector", [3, 10])
    def test_nonnegative_out_of_range_raises(self, selector):
        with pytest.raises(ValueError, match=rf"row selector position {selector} out of range"):
            resolve_i(
                selector,
                nhead=1,
                group_positions=set(),
                n_merged_body=3,
                has_header=True,
            )

    def test_out_of_range_in_mixed_list_uses_same_error(self):
        with pytest.raises(ValueError, match="row selector position 3 out of range"):
            resolve_i(
                ["header", 3],
                nhead=1,
                group_positions=set(),
                n_merged_body=3,
                has_header=True,
            )

    def test_scalar_bool_is_not_an_integer_position(self):
        with pytest.raises(TypeError, match="bad row selector type: bool"):
            resolve_i(
                True,
                nhead=1,
                group_positions=set(),
                n_merged_body=3,
                has_header=True,
            )

    def test_negative_is_not_public(self):
        with pytest.raises(ValueError, match="negative row selectors are not supported"):
            resolve_i(-1, nhead=1, group_positions=set(), n_merged_body=3, has_header=True)

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError):
            resolve_i("bogus", nhead=1, group_positions=set(), n_merged_body=3, has_header=True)


class TestResolveJ:
    COLS = ["A", "B", "name", "value"]

    def test_none(self):
        assert resolve_j(None, self.COLS) == [1, 2, 3, 4]

    def test_str_exact_name(self):
        assert resolve_j("A", self.COLS) == [1]
        assert resolve_j("value", self.COLS) == [4]

    def test_str_regex_single(self):
        assert resolve_j("am", self.COLS, regex=True) == [3]

    def test_str_regex_multi(self):
        assert resolve_j("a", self.COLS, regex=True) == [3, 4]

    def test_str_exact_miss_raises(self):
        with pytest.raises(ValueError, match="column not found"):
            resolve_j("zzz", self.COLS)

    def test_str_regex_no_match_raises(self):
        with pytest.raises(ValueError, match="regex matched no columns"):
            resolve_j("zzz", self.COLS, regex=True)

    def test_str_regex_invalid_raises(self):
        with pytest.raises(ValueError, match="invalid regex pattern"):
            resolve_j("[", self.COLS, regex=True)

    def test_str_regex_too_long_raises(self):
        with pytest.raises(ValueError, match=r"501 characters \(maximum 500\)"):
            resolve_j("a" * 501, self.COLS, regex=True)

    def test_list_regex_too_long_raises(self):
        with pytest.raises(ValueError, match="regex pattern is too long"):
            resolve_j(["A", "a" * 501], self.COLS, regex=True)

    def test_list_regex_each_element(self):
        assert resolve_j(["am", "v"], self.COLS, regex=True) == [3, 4]
        assert resolve_j(["A", "na"], self.COLS, regex=True) == [1, 3]

    def test_list_regex_no_match_raises(self):
        with pytest.raises(ValueError, match="regex matched no columns"):
            resolve_j(["zzz", "yyy"], self.COLS, regex=True)

    def test_list_of_names(self):
        assert resolve_j(["A", "B"], self.COLS) == [1, 2]

    def test_list_of_ints(self):
        assert resolve_j([0, 2], self.COLS) == [1, 3]

    def test_mixed_name_and_position_list(self):
        assert resolve_j(["A", 2], self.COLS) == [1, 3]

    @pytest.mark.parametrize("selector", [-1, 4, 10])
    def test_integer_position_out_of_range(self, selector):
        with pytest.raises(ValueError, match=rf"column selector position {selector} out of range"):
            resolve_j(selector, self.COLS)

    def test_out_of_range_in_mixed_list_uses_same_error(self):
        with pytest.raises(ValueError, match="column selector position 4 out of range"):
            resolve_j(["A", 4], self.COLS)

    @pytest.mark.parametrize("selector", [True, ["A", True], ["A", 1.5], [object()]])
    def test_invalid_elements_are_rejected(self, selector):
        with pytest.raises(TypeError, match="column selector elements must be integers or strings"):
            resolve_j(selector, self.COLS)

    def test_list_name_not_found_raises(self):
        with pytest.raises(ValueError):
            resolve_j(["A", "ZZZ"], self.COLS)


class TestResolveIListOfStrings:
    def test_single_string_in_list(self):
        assert resolve_i(
            ["header"], nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [0]

    def test_mixed_strings(self):
        result = resolve_i(
            ["header", "data"], nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        )
        assert result == [0, 1, 2, 3]

    def test_groupi_and_data_are_canonical_and_deduplicated(self):
        result = resolve_i(
            ["groupi", "data", "groupi"],
            nhead=1,
            group_positions={2},
            n_merged_body=4,
            has_header=True,
        )
        assert result == [1, 2, 3, 4]

    def test_empty_string_list(self):
        assert resolve_i([], nhead=1, group_positions=set(), n_merged_body=3, has_header=True) == []

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError):
            resolve_i(["bogus"], nhead=1, group_positions=set(), n_merged_body=3, has_header=True)

    def test_with_ints(self):
        assert resolve_i(
            ["header", 0, 1], nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [0, 1, 2]


class TestResolveIDataDriven:
    DF = pl.DataFrame({"Score": [95, 72, 88, 60], "Grade": ["A", "C", "B", "D"]})

    def test_polars_expr(self):
        result = resolve_i(
            pl.col("Score") > 80,
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [1, 3]

    def test_polars_expr_no_match(self):
        result = resolve_i(
            pl.col("Score") > 200,
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == []

    def test_polars_expr_match_all(self):
        result = resolve_i(
            pl.col("Score") > 0,
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [1, 2, 3, 4]

    def test_polars_series(self):
        mask = pl.Series("m", [True, False, True, False])
        result = resolve_i(
            mask,
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [1, 3]

    def test_boolean_list(self):
        result = resolve_i(
            [True, False, True, False],
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [1, 3]

    def test_boolean_tuple(self):
        result = resolve_i(
            (False, True, False, True),
            nhead=1,
            group_positions={2, 5},
            n_merged_body=6,
            has_header=True,
            data=self.DF,
        )
        assert result == [3, 6]

    @pytest.mark.parametrize("mask", [[True, 1, False, 2], [True, "header", False, 2]])
    def test_boolean_mask_rejects_mixed_selector_types(self, mask):
        with pytest.raises(TypeError, match="cannot mix"):
            resolve_i(
                mask,
                nhead=1,
                group_positions=set(),
                n_merged_body=4,
                has_header=True,
                data=self.DF,
            )

    def test_boolean_list_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="length 3, expected 4"):
            resolve_i(
                [True, False, True],
                nhead=1,
                group_positions=set(),
                n_merged_body=4,
                has_header=True,
                data=self.DF,
            )

    def test_polars_series_rejects_non_boolean_dtype(self):
        with pytest.raises(TypeError, match="must have Boolean dtype"):
            resolve_i(
                pl.Series([1, 0, 1, 0]),
                nhead=1,
                group_positions=set(),
                n_merged_body=4,
                has_header=True,
                data=self.DF,
            )

    def test_polars_series_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="length 3, expected 4"):
            resolve_i(
                pl.Series([True, False, True]),
                nhead=1,
                group_positions=set(),
                n_merged_body=4,
                has_header=True,
                data=self.DF,
            )

    def test_callable(self):
        result = resolve_i(
            lambda row: row["Grade"] == "D",
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [4]

    def test_callable_height_mismatch_ok(self):
        """Callable filters independently; series length need not match merged body."""

        def pred(row):
            return row["Score"] % 2 == 0

        result = resolve_i(
            pred,
            nhead=1,
            group_positions=set(),
            n_merged_body=4,
            has_header=True,
            data=self.DF,
        )
        assert result == [2, 3, 4]

    def test_expression_skipped_when_data_is_none(self):
        """Without data, pl.Expr/Series/callable fall through to TypeError."""
        with pytest.raises(TypeError):
            resolve_i(
                pl.col("Score") > 80,
                nhead=1,
                group_positions=set(),
                n_merged_body=4,
                has_header=True,
            )

    def test_with_row_groups_maps_indices(self):
        df = pl.DataFrame({"v": [10, 20, 30, 40]})
        result = resolve_i(
            pl.col("v") > 15,
            nhead=1,
            group_positions={2, 5},
            n_merged_body=6,
            has_header=True,
            data=df,
        )
        assert result == [3, 4, 6]


class TestMapOriginalToInternal:
    def test_no_groups(self):
        assert _map_original_to_internal([0, 1, 2], set()) == [1, 2, 3]

    def test_empty_indices(self):
        assert _map_original_to_internal([], {2, 5}) == []

    def test_with_groups(self):
        result = _map_original_to_internal([0, 1, 2, 3], {2, 5})
        assert result == [1, 3, 4, 6]

    def test_group_before_first_row(self):
        result = _map_original_to_internal([0, 1], {1})
        assert result == [2, 3]

    def test_unsorted_indices(self):
        result = _map_original_to_internal([3, 0, 2], {3})
        assert result == [1, 4, 5]
