import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._format import _apply_escape, _apply_replace, _matches


@pytest.mark.typst
class TestDigits:
    def test_decimal(self):
        df = pl.DataFrame({"v": [3.14159, 2.71828]})
        out = tt(df).fmt(j="v", digits=2).render("typst")
        assert "3.14" in out
        assert "2.72" in out
        assert_snapshot("fmt_decimal", out)

    def test_significant(self):
        df = pl.DataFrame({"v": [3.14159, 0.00123]})
        out = tt(df).fmt(j="v", digits=3, num_fmt="significant").render("typst")
        assert "3.14" in out
        assert "0.00123" in out
        assert_snapshot("fmt_significant", out)

    def test_integer_ignores_digits(self):
        df = pl.DataFrame({"x": [10, 20, 30]})
        out = tt(df).fmt(j="x", digits=2).render("typst")
        assert "10" in out
        assert "20" in out
        assert "30" in out

    def test_digits_none_no_effect(self):
        df = pl.DataFrame({"v": [3.14159, 2.71828]})
        out = tt(df).fmt(j="v").render("typst")
        assert "3.14159" in out


@pytest.mark.typst
class TestReplace:
    def test_replace_true(self):
        df = pl.DataFrame({"x": [None, 10], "y": [1.0, 2.0]})
        t = tt(df).fmt(replace=True).render("typst")
        assert t  # no crash

    def test_replace_str(self):
        df = pl.DataFrame({"x": [None, 10], "y": [1.0, 2.0]})
        out = tt(df).fmt(replace="—").render("typst")
        assert "\\u2014" in out or "\\—" in out or "\\u2014" in out or "—" in out

    def test_replace_dict_none(self):
        df = pl.DataFrame({"x": [None, 10, None]})
        out = tt(df).fmt(replace={None: "MISSING"}).render("typst")
        assert "MISSING" in out

    def test_replace_dict_nan(self):
        df = pl.DataFrame({"x": [float("nan"), 10.0]})
        out = tt(df).fmt(replace={float("nan"): "NAN"}).render("typst")
        assert "NAN" in out

    def test_replace_dict_inf(self):
        df = pl.DataFrame({"x": [float("inf"), 10.0]})
        out = tt(df).fmt(replace={float("inf"): "INF"}).render("typst")
        assert "INF" in out


class TestFormattingUtilities:
    @pytest.mark.parametrize(
        ("key", "typed", "rendered"),
        [
            (None, None, ""),
            (float("nan"), float("nan"), "nan"),
            (float("inf"), float("inf"), "inf"),
            (float("-inf"), float("-inf"), "-inf"),
            ("null", None, ""),
            ("nan", float("nan"), "nan"),
            ("inf", float("inf"), "inf"),
            ("-inf", float("-inf"), "-inf"),
            (7, 7, "7"),
            ("7", 7, "7"),
        ],
    )
    def test_matches_special_and_regular_values(self, key, typed, rendered):
        assert _matches(key, typed, rendered)

    def test_matches_distinguishes_infinity_signs(self):
        assert not _matches(float("inf"), float("-inf"), "-inf")

    @pytest.mark.parametrize(
        ("typed", "rendered", "replace", "expected"),
        [
            (None, "", True, " "),
            (float("nan"), "nan", "missing", "missing"),
            (1, "1", "missing", "1"),
            (None, "", {None: "NA"}, "NA"),
            (float("inf"), "inf", {"inf": "infinity"}, "infinity"),
            (2, "2", {1: "one"}, "2"),
        ],
    )
    def test_apply_replace(self, typed, rendered, replace, expected):
        assert _apply_replace(typed, rendered, replace) == expected

    @pytest.mark.parametrize(
        ("value", "escape_spec", "output", "expected"),
        [
            ("a#b", True, "typst", "a\\#b"),
            ("a<b", True, "html", "a&lt;b"),
            ("a&b", "typst", "ascii", "a&amp;b"),
            ("a#b", False, "typst", "a#b"),
        ],
    )
    def test_apply_escape(self, value, escape_spec, output, expected):
        assert _apply_escape(value, escape_spec, output) == expected


@pytest.mark.typst
class TestEscape:
    def test_fmt_escape_true(self):
        df = pl.DataFrame({"A": ["#hash", "delta$"]})
        out = tt(df, escape=False).fmt(escape=True).render("typst")
        assert "\\#" in out
        assert "\\$" in out

    def test_fmt_escape_false_with_global_escape(self):
        df = pl.DataFrame({"A": ["#hash"]})
        out = tt(df, escape=True).fmt(escape=False).render("typst")
        assert "\\#" in out


@pytest.mark.typst
class TestFn:
    def test_empty_row_selector_does_not_fall_back_to_body(self):
        df = pl.DataFrame({"value": [1, 2]})
        out = tt(df).theme_empty().fmt(i=[], fn=lambda vec: ["changed"] * len(vec)).render("typst")
        assert "changed" not in out
        assert "[1]" in out
        assert "[2]" in out

    def test_fn_column_transform(self):
        df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
        out = tt(df).fmt(j="x", fn=lambda vec: [f"#{v}" for v in vec]).render("typst")
        assert "\\#1" in out
        assert "\\#2" in out
        assert "\\#3" in out

    def test_fn_returns_wrong_length(self):
        df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
        t = tt(df).fmt(j="x", fn=lambda vec: ["only one"])
        with pytest.raises(ValueError, match="returned 1 items"):
            t.render("typst")

    def test_fn_on_body(self):
        df = pl.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        out = tt(df).fmt(fn=lambda vec: [f"x{v}" for v in vec]).render("typst")
        assert "x1" in out
        assert "x3" in out

    def test_fn_on_header(self):
        df = pl.DataFrame({"first": [1], "second": [2]})
        out = (
            tt(df)
            .fmt(i="header", j="first", fn=lambda vec: [value.upper() for value in vec])
            .render("typst")
        )
        assert "[FIRST]" in out
        assert "[second]" in out

    def test_fn_on_header_of_empty_table(self):
        df = pl.DataFrame(schema={"value": pl.Int64})
        out = tt(df).theme_empty().fmt(i="header", fn=lambda vec: ["renamed"]).render("typst")
        assert "[renamed]" in out

    def test_fn_on_header_and_body(self):
        df = pl.DataFrame({"value": [1, 2]})
        out = tt(df).fmt(i="all", fn=lambda vec: [f"x{value}" for value in vec]).render("typst")
        assert "[xvalue]" in out
        assert "[x1]" in out
        assert "[x2]" in out

    def test_stacked_fn_and_escape_on_header(self):
        df = pl.DataFrame({"value": [1]})
        out = (
            tt(df, escape=False)
            .fmt(i="header", fn=lambda vec: [f"#{value}" for value in vec])
            .fmt(i="header", escape=True)
            .render("typst")
        )
        assert "[\\#value]" in out


@pytest.mark.typst
class TestPipeline:
    def test_pipeline_order_numeric_then_fn(self):
        df = pl.DataFrame({"v": [3.14159, 2.71828]})
        out = tt(df).fmt(j="v", digits=2, fn=lambda vec: [f"{v}x" for v in vec]).render("typst")
        assert "3.14x" in out
        assert "2.72x" in out

    def test_pipeline_order_replace_before_escape(self):
        df = pl.DataFrame({"A": ["hello", None]})
        out = tt(df, escape=False).fmt(replace={None: "say #hi"}, escape=True).render("typst")
        assert "\\#hi" in out

    def test_stacked_fmt_calls(self):
        df = pl.DataFrame({"v": [3.14159, 2.71828]})
        out = (
            tt(df)
            .fmt(j="v", digits=2)
            .fmt(j="v", fn=lambda vec: [f"[{v}]" for v in vec])
            .render("typst")
        )
        assert "\\[3.14\\]" in out


@pytest.mark.typst
class TestSnapshots:
    def test_fmt_full(self):
        df = pl.DataFrame(
            {
                "name": ["alice", "bob"],
                "score": [3.14159, 2.71828],
                "status": [None, "ok"],
            }
        )
        out = tt(df).fmt(j="score", digits=2).fmt(j="status", replace="—").render("typst")
        assert_snapshot("fmt_full", out)

    def test_preformatted_polars(self):
        df = pl.DataFrame({"pct": [0.1234, 0.5678]}).with_columns(
            (pl.col("pct") * 100).round(1).cast(pl.Utf8).alias("display")
        )
        out = tt(df.select("display")).render("typst")
        assert "12.3" in out
        assert "56.8" in out
        assert_snapshot("fmt_preformatted", out)
