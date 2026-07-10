import pytest

from tytable._indices import convert_col_to_typst, convert_row_to_typst


class TestConvertRowToTypst:
    def test_nhead_1(self):
        # nhead=1: i=0->0, 1->1, 2->2
        assert convert_row_to_typst(0, 1) == 0
        assert convert_row_to_typst(1, 1) == 1
        assert convert_row_to_typst(2, 1) == 2

    def test_nhead_3(self):
        # nhead=3: -2->0, -1->1, 0->2, 1->3, 2->4
        assert convert_row_to_typst(-2, 3) == 0
        assert convert_row_to_typst(-1, 3) == 1
        assert convert_row_to_typst(0, 3) == 2
        assert convert_row_to_typst(1, 3) == 3
        assert convert_row_to_typst(2, 3) == 4

    def test_nhead_0(self):
        assert convert_row_to_typst(1, 0) == 0

    def test_nhead_0_raises(self):
        with pytest.raises(ValueError):
            convert_row_to_typst(0, 0)
        with pytest.raises(ValueError):
            convert_row_to_typst(-1, 0)


class TestConvertColToTypst:
    def test_basic(self):
        assert convert_col_to_typst(1) == 0
        assert convert_col_to_typst(5) == 4
