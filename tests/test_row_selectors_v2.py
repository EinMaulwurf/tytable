import polars as pl
import pytest

from tytable import tt
from tytable._resolve import build

DF = pl.DataFrame({"a": [10, 20, 30], "b": [1, 2, 3]})


def grouped_table():
    return tt(DF).theme_plain().group(i={"before": 0, "middle": 1, "after": 3})


def test_omitted_style_selector_targets_only_source_data():
    built = build(grouped_table().style(background="gray"), "typst")
    assert {cell for cell, props in built.style_grid.items() if props.get("background")} == {
        (2, 0),
        (2, 1),
        (4, 0),
        (4, 1),
        (5, 0),
        (5, 1),
    }


def test_all_explicitly_includes_headers_and_synthetic_rows():
    built = build(
        grouped_table().group(j={"columns": ["a", "b"]}).style(i="all", bold=True),
        "typst",
    )
    assert {i for i, _ in built.style_grid} == set(range(8))


@pytest.mark.parametrize("method", ["style", "fmt", "images"])
def test_integer_selectors_keep_source_identity_past_groups(method):
    table = grouped_table()
    if method == "style":
        built = build(table.style(i=1, j="a", bold=True), "typst")
        assert built.style_grid[(4, 0)]["bold"] is True
        assert (2, 0) not in built.style_grid
    elif method == "fmt":
        built = build(table.fmt(i=1, j="a", replace={20: "selected"}), "typst")
        assert built.data_body[3][0] == "selected"
        assert built.data_body[1][0] == "10"
    else:
        built = build(table.images(i=1, j="a", paths=["one.png"]), "ascii")
        assert built.data_body[3][0] == "[image]"
        assert built.data_body[1][0] == "10"


def test_repeated_rows_and_columns_are_deduplicated_in_display_order():
    built = build(
        grouped_table().images(
            i=[2, 0, 2, 0],
            j=["b", "a", "b"],
            paths=["1", "2", "3", "4"],
        ),
        "ascii",
    )
    assert built.data_body[1] == ["[image]", "[image]"]
    assert built.data_body[4] == ["[image]", "[image]"]


@pytest.mark.parametrize(
    ("operation", "match"),
    [
        (lambda table: table.fmt(i="groupj", replace=True), r"\.fmt\(\).*'groupj'"),
        (
            lambda table: table.images(i="header", j="a", paths=["one.png"]),
            r"\.images\(\).*'header'",
        ),
        (
            lambda table: table.plot(i="header", j="a", fun=lambda value: value),
            r"\.plot\(\).*'header'",
        ),
    ],
)
def test_content_operations_reject_unsupported_row_kinds(operation, match):
    table = operation(tt(DF).theme_plain().group(j={"columns": ["a", "b"]}))
    with pytest.raises(ValueError, match=match):
        build(table, "ascii")


def test_targeted_notes_reject_column_group_rows():
    table = tt(
        DF,
        notes=[{"text": "not representable", "i": "groupj", "j": "a"}],
    ).group(j={"columns": ["a", "b"]})
    with pytest.raises(ValueError, match="targeted notes.*'groupj'"):
        build(table, "typst")


def test_targeted_note_defaults_missing_axis_to_data_region():
    built = build(
        tt(
            DF,
            notes=[{"text": "column", "j": "a"}, {"text": "row", "i": 1}],
        )
        .theme_plain()
        .group(i={"before": 0, "middle": 1, "after": 3}),
        "typst",
    )
    assert "#super[1]" not in built.data_body[0][0]
    assert "#super[1]" in built.data_body[1][0]
    assert "#super[1]" in built.data_body[3][0]
    assert "#super[1]" in built.data_body[4][0]
    assert "#super[2]" in built.data_body[3][0]
    assert "#super[2]" in built.data_body[3][1]


@pytest.mark.parametrize("selector", ["body", "~groupi", -1, [0, -1]])
def test_removed_row_selectors_raise(selector):
    with pytest.raises(ValueError):
        build(tt(DF).style(i=selector, bold=True), "typst")
