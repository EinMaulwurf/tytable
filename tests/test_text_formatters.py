"""Behavioral coverage of text factories, composition, and v5 migration boundaries."""

from decimal import Decimal

import polars as pl
import pytest

from tytable import tt
from tytable.formatters import linebreak, math, missing, number, replace, scientific


def test_replacement_is_exact_and_copies_mapping():
    mapping = {1: "one", "null": "literal", None: "absent"}
    formatter = replace(mapping)
    mapping[1] = "changed"
    assert formatter([1, "1", None, "null", "nan", [1]]) == [
        "one",
        "1",
        "absent",
        "literal",
        "nan",
        [1],
    ]


def test_missing_handles_numeric_nan_and_preserves_literal_strings():
    assert missing()([None, float("nan"), Decimal("NaN"), "nan", "null", 0, float("inf")]) == [
        "—",
        "—",
        "—",
        "nan",
        "null",
        0,
        float("inf"),
    ]
    assert missing("")([None]) == [""]


def test_typed_and_display_replacements_are_explicit():
    df = pl.DataFrame({"value": [1.25, 2.5]})
    table = tt(df).fmt(fn=number(digits=1)).fmt(fn=replace({"1.2": "rounded"}), fn_values="display")
    assert "rounded" in table.render("ascii")
    assert "2.5" in table.render("ascii")
    table.fmt(fn=replace({1.25: "original"}))
    assert "original" in table.render("ascii")


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_semantic_content_survives_identity_missing_and_unmatched_replacement(output):
    table = tt(pl.DataFrame({"value": [1250]})).fmt(fn=scientific())
    expected = table.render(output)
    for callback in (
        lambda values: values,
        missing(),
        replace({"absent": "other"}),
        linebreak("#"),
    ):
        table.fmt(fn=callback, fn_values="display")
        assert table.render(output) == expected


@pytest.mark.parametrize("output", ["typst", "html", "ascii"])
def test_changing_native_output_returns_to_plain_text(output):
    table = tt(pl.DataFrame({"value": [1250]})).fmt(fn=scientific())
    table.fmt(fn=lambda values: ["<tag>$#"], fn_values="display")
    result = table.render(output)
    assert {"typst": r"\<tag\>\$\#", "html": "&lt;tag&gt;$#", "ascii": "<tag>$#"}[output] in result


@pytest.mark.parametrize("reverse", [False, True])
def test_math_linebreak_composition_in_both_orders(reverse):
    callbacks = [linebreak("|"), math()]
    if reverse:
        callbacks.reverse()
    table = tt(pl.DataFrame({"formula": ["x = 1|y = 2"]})).theme_plain()
    table.fmt(fn=callbacks[0]).fmt(fn=callbacks[1], fn_values="display")
    assert r"[$x = 1 \ y = 2$]" in table.render("typst")
    assert "x = 1<br>y = 2" in table.render("html")
    assert "x = 1|y = 2" in table.render("ascii")


def test_multiple_break_markers_do_not_modify_generated_markup():
    table = tt(pl.DataFrame({"text": ["a|b#c&"]})).theme_plain()
    table.fmt(fn=linebreak("|")).fmt(fn=linebreak("#"), fn_values="display")
    assert r"[a \ b \ c&]" in table.render("typst")
    assert "a<br>b<br>c&amp;" in table.render("html")
    table.fmt(fn=linebreak("&"), fn_values="display")
    assert "a<br>b<br>c<br>" in table.render("html")


def test_math_display_null_and_direct_call():
    assert math()(["x^2", None]) == ["x^2", "—"]
    table = (
        tt(pl.DataFrame({"formula": ["$x^2$", None]}))
        .theme_plain()
        .fmt(fn=math(display=True, null="$"))
    )
    assert "[$ x^2 $]" in table.render("typst")
    assert r"[\$]" in table.render("typst")
    assert "$x^2$" in table.render("html")


def test_linebreak_respects_global_escape_false():
    table = tt(pl.DataFrame({"text": ["<b>one</b>|two"]}), escape=False).fmt(fn=linebreak("|"))
    assert "<b>one</b><br>two" in table.render("html")


@pytest.mark.parametrize(
    "keyword,value", [("replace", {}), ("math", True), ("escape", True), ("linebreak", "|")]
)
def test_removed_keywords_are_rejected(keyword, value):
    with pytest.raises(TypeError, match="unexpected keyword"):
        tt(pl.DataFrame({"value": [1]})).fmt(**{keyword: value})


@pytest.mark.parametrize(
    "factory,kwargs",
    [
        (replace, {"mapping": []}),
        (missing, {"label": None}),
        (math, {"display": "yes"}),
        (math, {"null": None}),
        (linebreak, {"marker": 1}),
    ],
)
def test_factory_configuration_is_validated_immediately(factory, kwargs):
    with pytest.raises(TypeError):
        factory(**kwargs)


def test_filters_and_structural_rows():
    table = tt(pl.DataFrame({"a|b": ["x|y", "u|v"]})).theme_plain()
    table.fmt(i="header", fn=linebreak("|"))
    table.fmt(j="a|b", where=pl.col("a|b") == "x|y", fn=linebreak("|"), output="html")
    html = table.render("html")
    assert "a<br>b" in html and "x<br>y" in html and "u|v" in html
    assert "x|y" in table.render("typst")


def test_scientific_math_retains_native_notation_and_escaped_labels():
    table = tt(pl.DataFrame({"x": [1250]})).fmt(fn=scientific(decimal_mark="<>&#"))
    table.fmt(fn=math(), fn_values="display")
    assert r"$#box[1\<\>&\#25 × 10#super[3]]$" in table.render("typst")
    assert "1&lt;&gt;&amp;#25 × 10<sup>3</sup>" in table.render("html")
    assert missing()([Decimal("sNaN")]) == ["—"]
