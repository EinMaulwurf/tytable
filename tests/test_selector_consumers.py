import polars as pl
import polars.selectors as cs
import pytest

from tytable import tt
from tytable._resolve import build
from tytable.selectors import colgroup, regex


@pytest.mark.parametrize(
    "selector_factory",
    [
        lambda: regex(r"^target_"),
        lambda: cs.starts_with("target_"),
        lambda: colgroup(label="Targets", level=0),
    ],
    ids=["regex", "polars", "colgroup"],
)
def test_column_selectors_work_across_every_j_consumer(selector_factory):
    """Keep the public promise that column selectors work anywhere ``j`` does."""
    data = pl.DataFrame({"target_a": [1], "target_b": [2], "other": [3]})

    def table():
        return tt(data).theme_plain().group(j={"Targets": ["target_a", "target_b"]})

    styled = build(table().style(i=0, j=selector_factory(), bold=True), "ascii")
    assert styled.style_grid[(2, 0)]["bold"] is True
    assert styled.style_grid[(2, 1)]["bold"] is True
    assert "bold" not in styled.style_grid.get((2, 2), {})

    formatted = build(
        table().fmt(i=0, j=selector_factory(), replace={1: "selected", 2: "selected"}),
        "ascii",
    )
    assert formatted.data_body == [["selected", "selected", "3"]]

    plotted = table().plot(
        i=0,
        j=selector_factory(),
        fun=lambda value: value,
        data=["first", "second"],
    )
    assert build(plotted, "ascii").data_body == [["[plot]", "[plot]", "3"]]

    imaged = table().images(
        i=0,
        j=selector_factory(),
        paths=["first.png", "second.png"],
    )
    assert build(imaged, "ascii").data_body == [["[image]", "[image]", "3"]]

    noted = tt(
        data,
        notes=[{"text": "Selected", "i": 0, "j": selector_factory()}],
    ).group(j={"Targets": ["target_a", "target_b"]})
    assert build(noted, "typst").data_body == [["1#super[1]", "2#super[1]", "3"]]

    renamed = build(table().set_name(j=selector_factory(), name="Selected"), "ascii")
    assert renamed.colnames_display == ["Selected", "Selected", "other"]

    projected = build(table().show_columns(selector_factory()), "ascii")
    assert projected.colnames_display == ["target_a", "target_b"]

    regrouped = build(table().group(j={"Outer": selector_factory()}), "ascii")
    assert regrouped.col_groups == [
        ["Outer", "", None],
        ["Targets", "", None],
    ]
