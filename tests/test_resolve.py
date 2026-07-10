import pytest

from tytable._indices import resolve_i, resolve_j


class TestResolveI:
    def test_none_returns_none(self):
        assert (
            resolve_i(None, nhead=1, group_positions=set(), n_merged_body=3, has_header=True)
            is None
        )

    def test_header(self):
        assert resolve_i(
            "header", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [0]
        assert (
            resolve_i("header", nhead=0, group_positions=set(), n_merged_body=3, has_header=False)
            == []
        )

    def test_body(self):
        assert resolve_i(
            "body", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
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
        assert resolve_i(
            "~groupi", nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [1, 2, 3]

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
            "~groupi", nhead=1, group_positions={2}, n_merged_body=4, has_header=True
        ) == [1, 3, 4]

    def test_numeric(self):
        assert resolve_i(0, nhead=1, group_positions=set(), n_merged_body=3, has_header=True) == [1]
        assert resolve_i(2, nhead=1, group_positions=set(), n_merged_body=3, has_header=True) == [3]

    def test_numeric_list(self):
        assert resolve_i(
            [0, 1, 2], nhead=1, group_positions=set(), n_merged_body=3, has_header=True
        ) == [1, 2, 3]

    def test_negative_out_of_range_raises(self):
        with pytest.raises(ValueError):
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
        assert resolve_j("am", self.COLS) == [3]

    def test_str_regex_multi(self):
        assert resolve_j("a", self.COLS) == [3, 4]

    def test_list_of_names(self):
        assert resolve_j(["A", "B"], self.COLS) == [1, 2]

    def test_list_of_ints(self):
        assert resolve_j([0, 2], self.COLS) == [1, 3]

    def test_list_name_not_found_raises(self):
        with pytest.raises(ValueError):
            resolve_j(["A", "ZZZ"], self.COLS)
