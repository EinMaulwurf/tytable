import pytest

from tytable._utils import format_markup_num


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (-12, "-12"),
        (1.0, "1"),
        (-2.0, "-2"),
        (1.25, "1.25"),
        (True, "true"),
        (False, "false"),
        (None, ""),
        (1 + 2j, "(1+2j)"),
    ],
)
def test_format_markup_num(value, expected):
    assert format_markup_num(value) == expected
