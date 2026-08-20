import polars as pl
import polars.selectors as cs
import pytest

from tytable import regex, tt
from tytable._resolve import build


def test_show_columns_accepts_mixed_selectors_in_source_order():
    df = pl.DataFrame(
        {
            "helper": [True, False],
            "name": ["Ada", "Lin"],
            "score": [2.5, 3.5],
            "rank": [1, 2],
        }
    )

    built = build(tt(df).show_columns(["rank", cs.string(), cs.numeric(), "name"]), "ascii")

    assert built.colnames_display == ["name", "score", "rank"]
    assert built.data_body == [["Ada", "2.5", "1"], ["Lin", "3.5", "2"]]


def test_show_columns_accepts_regex_selector():
    df = pl.DataFrame({"Q1": [1], "Q2": [2], "Total": [3]})

    built = build(tt(df).show_columns(regex(r"^Q")), "ascii")

    assert built.colnames_display == ["Q1", "Q2"]


def test_show_columns_invert_hides_the_combined_selection():
    df = pl.DataFrame({"name": ["Ada"], "_flag": [True], "score": [2.5]})

    built = build(
        tt(df).show_columns(["score", cs.starts_with("_")], invert=True),
        "ascii",
    )

    assert built.colnames_display == ["name"]
    assert built.data_body == [["Ada"]]


def test_show_columns_replaces_previous_projection_and_clone_is_independent():
    base = tt(pl.DataFrame({"a": [1], "b": [2], "c": [3]})).show_columns(["a", "b"])
    clone = base.clone().show_columns("c")
    base.show_columns("b")

    assert build(base, "ascii").colnames_display == ["b"]
    assert build(clone, "ascii").colnames_display == ["c"]


def test_hidden_helper_column_remains_available_to_where():
    table = (
        tt(pl.DataFrame({"name": ["Ada", "Lin"], "warning": [True, False]}))
        .style(
            j="name",
            where=pl.col("warning").alias("name"),
            bold=True,
        )
        .show_columns("warning", invert=True)
    )

    built = build(table, "typst")

    assert built.colnames_display == ["name"]
    assert built.style_grid[(1, 0)]["bold"] is True
    assert "bold" not in built.style_grid.get((2, 0), {})


def test_show_columns_projects_widths_alignments_and_cell_styles():
    table = (
        tt(
            pl.DataFrame({"a": [1], "b": ["x"], "c": [3.0]}),
            width=[0.2, "2cm", None],
        )
        .theme_plain()
        .style(i=0, j="c", italic=True, line="lr")
        .show_columns(["b", "c"])
    )

    built = build(table, "html")

    assert built.width == ["2cm", None]
    assert built.column_alignments == ["l", "r"]
    assert built.style_grid[(1, 1)]["italic"] is True
    assert [(line["j"], line["line"]) for line in built.style_lines] == [(1, "lr")]


def test_show_columns_shrinks_and_removes_column_groups():
    df = pl.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    table = tt(df).group(j={"Numbers": ["b", "c"]})

    partial = build(table.clone().show_columns(["c", "d"]), "typst")
    removed = build(table.clone().show_columns("d"), "typst")

    assert partial.col_groups == [["Numbers", None]]
    assert partial.layout.column_group_rows == 1
    assert removed.col_groups == []
    assert removed.layout.column_group_rows == 0


def test_show_columns_keeps_row_group_label_when_first_source_column_is_hidden():
    table = (
        tt(pl.DataFrame({"hidden": [1, 2], "shown": [3, 4]}))
        .group(i={"Section": 1})
        .show_columns("shown")
    )

    built = build(table, "typst")

    assert built.data_body == [["3"], ["Section"], ["4"]]
    assert built.style_grid[(2, 0)]["colspan"] == 1
    assert built.style_grid[(2, 0)]["align"] == "l"


def test_show_columns_clips_span_only_when_its_anchor_remains_visible():
    df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
    table = tt(df).style(i=0, j="a", colspan=3)

    clipped = build(table.clone().show_columns(["a", "c"]), "html")
    unspanned = build(table.clone().show_columns(["b", "c"]), "html")

    assert clipped.style_grid[(1, 0)]["colspan"] == 2
    assert all("colspan" not in props for props in unspanned.style_grid.values())


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_show_columns_applies_to_every_renderer(output):
    rendered = (
        tt(pl.DataFrame({"visible": ["yes"], "secret": ["do not render"]}))
        .show_columns("visible")
        .render(output)
    )

    assert "visible" in rendered
    assert "yes" in rendered
    assert "secret" not in rendered
    assert "do not render" not in rendered


def test_show_columns_validates_invert():
    with pytest.raises(TypeError, match="invert must be a bool"):
        tt(pl.DataFrame({"a": [1]})).show_columns("a", invert=1)  # type: ignore[arg-type]


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_show_columns_accepts_an_empty_selection(output):
    rendered = tt(pl.DataFrame({"secret_column": [987654]})).show_columns([]).render(output)

    assert rendered
    assert "(empty table)" in rendered
    assert "secret_column" not in rendered
    assert "987654" not in rendered
