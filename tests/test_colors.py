import pytest

from tytable._colors import color_to_typst


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        ("red", 'rgb("#ff0000")'),
        ("ReBeCcApUrPlE", 'rgb("#663399")'),
        ("#f00", 'rgb("#ff0000")'),
        ("#f008", 'rgb("#ff000088")'),
        ("#12ABef", 'rgb("#12abef")'),
        ("#12ABef80", 'rgb("#12abef80")'),
        ("black", "black"),
        ("white", "white"),
    ],
)
def test_color_to_typst(color, expected):
    assert color_to_typst(color) == expected


@pytest.mark.parametrize("color", ["", "#12", "#ggg", "not-a-real-color"])
def test_color_to_typst_rejects_invalid_or_unknown_values(color):
    with pytest.raises(ValueError, match="invalid color value"):
        color_to_typst(color)
