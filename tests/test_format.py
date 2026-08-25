import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import polars as pl
import polars.selectors as cs
import pytest

from tests.helpers import assert_snapshot
from tytable import formatters, tt
from tytable._format import _apply_escape, _apply_replace, _matches
from tytable._resolve import build
from tytable.formatters import currency, duration, number, percent, unit
from tytable.formatters import date as date_formatter


class TestSemanticFormatters:
    @pytest.mark.parametrize("output", ["typst", "html", "ascii"])
    def test_german_number(self, output):
        df = pl.DataFrame({"value": [1023.87, -12.5, None]})

        rendered = tt(df).fmt(j="value", fn=number(locale="de_DE", digits=2)).render(output)

        assert "1.023,87" in rendered
        assert "-12,50" in rendered
        assert "—" in rendered

    def test_german_currency_and_percent(self):
        df = pl.DataFrame({"price": [1023.87], "share": [0.125]})

        rendered = (
            tt(df)
            .fmt(j="price", fn=currency("EUR", locale="de_DE"))
            .fmt(j="share", fn=percent(locale="de_DE", digits=1))
            .render("ascii")
        )

        assert "1.023,87 €" in rendered
        assert "12,5 %" in rendered

    def test_percent_uses_null_text_for_nan(self):
        assert percent(null="missing")([math.nan]) == ["missing"]

    def test_number_scale_is_applied_before_formatting(self):
        formatter = number(digits=1, scale=1 / 1e6, suffix=" million")

        assert formatter([2_500_000, -750_000, None]) == [
            "2.5 million",
            "-0.8 million",
            "—",
        ]

    def test_percent_scales_fractions_by_default(self):
        assert percent(digits=1)([0.6281]) == ["62.8%"]

    def test_currency_and_unit_accept_scale(self):
        assert currency("USD", digits=1, scale=1 / 1e6)([2_500_000]) == ["$2.5"]
        assert unit("g", digits=1, scale=1000)([1.25]) == ["1,250.0 g"]
        assert unit("g", digits=1, scale=1000, si_prefix=True)([1.25]) == ["1.2 kg"]

    @pytest.mark.parametrize(
        "factory",
        [
            lambda: number(scale=True),
            lambda: currency(scale="million"),
            lambda: percent(scale=None),
            lambda: unit("m", scale="kilo"),
        ],
    )
    def test_scale_rejects_non_numeric_values(self, factory):
        with pytest.raises(TypeError, match="scale must be numeric"):
            factory()

    def test_flexible_precision_and_negative_zero(self):
        formatter = number(digits=3, min_digits=0)

        assert formatter([1, 1.2, 1.2346, -0.0001]) == ["1", "1.2", "1.235", "0"]
        assert number(digits=2, normalize_negative_zero=False)([-0.001]) == ["-0.00"]

    def test_named_rounding_modes(self):
        assert number(digits=0, rounding="half_even")([2.5, 3.5]) == ["2", "4"]
        assert number(digits=0, rounding="half_up")([2.5, -2.5]) == ["3", "-3"]
        assert number(digits=0, rounding="floor")([2.9, -2.1]) == ["2", "-3"]

    def test_special_numeric_value_labels(self):
        formatter = number(nan="NA", inf="∞", negative_inf="−∞")

        assert formatter([math.nan, Decimal("NaN"), math.inf, -math.inf, None]) == [
            "NA",
            "NA",
            "∞",
            "−∞",
            "—",
        ]
        assert number(null="missing")([math.nan]) == ["missing"]

    def test_number_notations(self):
        assert number(digits=3, notation="significant")([1234, 0.01234]) == [
            "1,230",
            "0.0123",
        ]
        assert number(digits=2, min_digits=0, notation="scientific")([12345]) == ["1.23e+4"]
        assert number(digits=2, min_digits=0, notation="engineering")([12345]) == ["12.34e+3"]
        assert number(digits=1, min_digits=0, notation="scientific", locale="de_DE")([0.012]) == [
            "1,2e-2"
        ]

    def test_compact_labels_and_rounding_boundary(self):
        formatter = number(
            digits=1,
            compact=True,
            compact_labels={3: " thousand", 6: " million"},
        )

        assert formatter([2_500_000, 999_949, 999_950]) == [
            "2.5 million",
            "999.9 thousand",
            "1.0 million",
        ]

    def test_currency_forwards_number_options(self):
        assert currency("JPY", digits=None)([12.4]) == ["¥12"]
        assert currency(
            "USD",
            digits=1,
            min_digits=0,
            grouping=False,
            decimal_mark=",",
            thousands_mark="",
            symbol_position="suffix",
        )([1234.5]) == ["1234,5 $"]
        assert currency("USD", digits=1, compact=True)([2_500_000]) == ["$2.5M"]

    def test_percent_forwards_number_options(self):
        formatter = percent(digits=2, min_digits=0, rounding="half_up")

        assert formatter([0.625, -0.00001]) == ["62.5%", "0%"]

    def test_unit_iec_prefix_and_prefix_rollover(self):
        formatter = unit("B", digits=1, min_digits=0, iec_prefix=True)

        assert formatter([1024, 1_048_576]) == ["1 KiB", "1 MiB"]
        assert unit("g", digits=1, si_prefix=True)([999_949, 999_950]) == [
            "999.9 kg",
            "1.0 Mg",
        ]

    def test_human_duration_and_shared_numeric_options(self):
        formatter = duration(style="human", digits=1, min_digits=0)

        assert formatter([90_061.5, 90, 0]) == ["1d 1h 1m 1.5s", "1m 30s", "0s"]
        assert duration(digits=0, rounding="half_up")([59.5]) == ["00:01:00"]
        assert duration(digits=2, min_digits=0)([1.2]) == ["00:00:01.2"]
        assert duration(nan="NA", inf="forever")([math.nan, math.inf]) == ["NA", "forever"]

    def test_date_timezone_conversion(self):
        formatter = date_formatter("%Y-%m-%d %H:%M", timezone="America/New_York")

        assert formatter([datetime(2026, 1, 1, tzinfo=timezone.utc)]) == ["2025-12-31 19:00"]
        with pytest.raises(ValueError, match="timezone-aware"):
            formatter([datetime(2026, 1, 1)])

    @pytest.mark.parametrize(
        ("factory", "message"),
        [
            (lambda: number(digits=1, min_digits=2), "must not exceed"),
            (lambda: number(rounding="nearest"), "rounding must be one of"),
            (lambda: number(notation="binary"), "notation must be"),
            (lambda: number(compact_labels={0: "ones"}), "positive integers"),
            (lambda: number(compact=True, notation="scientific"), "cannot be combined"),
            (lambda: currency(symbol_position="left"), "symbol_position must be"),
            (lambda: unit("B", si_prefix=True, iec_prefix=True), "cannot both be true"),
            (lambda: duration(style="words"), "style must be"),
            (lambda: date_formatter(timezone=1), "timezone must be"),
        ],
    )
    def test_extended_formatter_options_are_validated(self, factory, message):
        with pytest.raises((TypeError, ValueError), match=message):
            factory()

    @pytest.mark.parametrize(
        ("factory", "message"),
        [
            (lambda: number(locale=[]), "locale must be a string or None"),
            (lambda: currency(1), "currency code must be a string"),
            (lambda: currency(symbol_position=[]), "symbol_position must be a string"),
            (lambda: date_formatter(1), "date pattern must be a string"),
            (lambda: duration(input_unit=[]), "input_unit must be a string"),
            (lambda: duration(style=[]), "style must be a string"),
            (lambda: unit(1), "unit symbol must be a string"),
        ],
    )
    def test_formatter_option_types_raise_contextual_type_errors(self, factory, message):
        with pytest.raises(TypeError, match=message):
            factory()

    def test_accounting_compact_and_custom_separators(self):
        accounting = number(digits=0, accounting=True)
        accounting_currency = currency("USD", digits=0, accounting=True)
        compact = number(digits=1, compact=True, decimal_mark=",", thousands_mark=".")

        assert accounting([-1250]) == ["(1,250)"]
        assert accounting_currency([-1250]) == ["($1,250)"]
        assert compact([2_500_000]) == ["2,5M"]

    def test_date(self):
        df = pl.DataFrame({"day": [date(2026, 8, 11), None]})
        rendered = tt(df).fmt(j="day", fn=date_formatter("%d.%m.%Y")).render("ascii")
        assert "11.08.2026" in rendered
        assert "—" in rendered

    def test_duration_accepts_numbers_and_timedeltas(self):
        formatter = duration(input_unit="minutes", digits=1)

        assert formatter([1.5, -61, None]) == ["00:01:30.0", "-01:01:00.0", "—"]
        assert duration(digits=3)([timedelta(days=1, microseconds=125_000)]) == ["24:00:00.125"]

    def test_duration_rounding_carries_between_clock_fields(self):
        assert duration(digits=1)([3599.96]) == ["01:00:00.0"]

    def test_unit_locale_si_prefix_and_accounting(self):
        formatter = unit("m", digits=1, locale="de_DE", si_prefix=True)

        assert formatter([1500, 0.002, 0, None]) == ["1,5 km", "2,0 mm", "0,0 m", "—"]
        assert unit("kg", digits=0, accounting=True)([-1250]) == ["(1,250 kg)"]

    @pytest.mark.parametrize("factory", [duration, lambda: unit("m")])
    def test_new_formatters_reject_non_numeric_values(self, factory):
        with pytest.raises(TypeError, match="requires numeric values"):
            factory()(["one"])

    def test_namespace_reexports_public_formatters(self):
        assert formatters.number is number
        assert formatters.currency is currency
        assert formatters.percent is percent
        assert formatters.date is date_formatter
        assert formatters.duration is duration
        assert formatters.unit is unit

    def test_invalid_number_value_has_clear_error(self):
        table = tt(pl.DataFrame({"value": ["one"]})).fmt(fn=number())
        with pytest.raises(TypeError, match="requires numeric values"):
            table.render()


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

    def test_scientific(self):
        df = pl.DataFrame({"v": [3141.59, 0.00123]})
        out = tt(df).fmt(j="v", digits=2, num_fmt="scientific").render("typst")
        assert "$3.14 times 10^3$" in out
        assert "$1.23 times 10^(-3)$" in out

    def test_scientific_formats_integers(self):
        df = pl.DataFrame({"x": [10, 200]})
        out = tt(df).fmt(j="x", digits=1, num_fmt="scientific").render("typst")
        assert "$1.0 times 10^1$" in out
        assert "$2.0 times 10^2$" in out

    def test_scientific_uses_html_markup(self):
        df = pl.DataFrame({"v": [3141.59, 0.00123]})
        out = tt(df).fmt(j="v", digits=2, num_fmt="scientific").render("html")
        assert "3.14 &times; 10<sup>3</sup>" in out
        assert "1.23 &times; 10<sup>-3</sup>" in out

    def test_scientific_remains_readable_in_ascii(self):
        df = pl.DataFrame({"v": [3141.59]})
        out = tt(df).fmt(j="v", digits=2, num_fmt="scientific").render("ascii")
        assert "3.14 * 10^3" in out

    def test_decimal_formats_integers(self):
        df = pl.DataFrame({"x": [10, 20, 30]})
        out = tt(df).fmt(j="x", digits=2).render("typst")
        assert "10.00" in out
        assert "20.00" in out
        assert "30.00" in out

    def test_significant_formats_integers(self):
        df = pl.DataFrame({"x": [1234, 5678]})
        out = tt(df).fmt(j="x", digits=2, num_fmt="significant").render("typst")

        assert "1.2e\\+03" in out
        assert "5.7e\\+03" in out

    def test_digits_none_no_effect(self):
        df = pl.DataFrame({"v": [3.14159, 2.71828]})
        out = tt(df).fmt(j="v").render("typst")
        assert "3.14159" in out

    @pytest.mark.parametrize("digits", [True, 1.5, "2"])
    def test_digits_rejects_non_integer(self, digits):
        with pytest.raises(TypeError, match="digits must be a non-negative integer"):
            tt(pl.DataFrame({"v": [1.0]})).fmt(digits=digits)

    def test_digits_rejects_negative_integer(self):
        with pytest.raises(ValueError, match="digits must be non-negative"):
            tt(pl.DataFrame({"v": [1.0]})).fmt(digits=-1)

    @pytest.mark.parametrize("num_fmt", ["currency", "", "Decimal"])
    def test_num_fmt_rejects_unknown_value(self, num_fmt):
        with pytest.raises(ValueError, match="num_fmt must be one of"):
            tt(pl.DataFrame({"v": [1.0]})).fmt(num_fmt=num_fmt)

    def test_num_fmt_rejects_non_string(self):
        with pytest.raises(TypeError, match="num_fmt must be a string"):
            tt(pl.DataFrame({"v": [1.0]})).fmt(num_fmt=None)  # type: ignore[arg-type]


class TestCellSelectors:
    DF = pl.DataFrame(
        {
            "Product": ["A", "B"],
            "Price": [150.25, 80.75],
            "Stock": [20.5, 200.75],
        }
    )

    def test_where_formats_individual_numeric_cells(self):
        built = build(tt(self.DF).fmt(where=cs.numeric() > 100, digits=0), "typst")

        assert built.data_body == [
            ["A", "150", "20.5"],
            ["B", "80.75", "201"],
        ]

    def test_without_where_keeps_row_column_cross_product(self):
        built = build(
            tt(self.DF).fmt(
                i=pl.col("Price") > 100,
                j=["Price", "Stock"],
                digits=0,
            ),
            "typst",
        )

        assert built.data_body == [
            ["A", "150", "20"],
            ["B", "80.75", "200.75"],
        ]

    def test_where_intersects_i_and_j(self):
        df = self.DF.with_columns(active=pl.Series([False, True]))
        built = build(
            tt(df).fmt(
                i=pl.col("active"),
                j=["Price", "Stock"],
                where=cs.numeric() > 100,
                digits=0,
            ),
            "typst",
        )

        assert built.data_body == [
            ["A", "150.25", "20.5", "false"],
            ["B", "80.75", "201", "true"],
        ]

    def test_where_filters_fn_inputs_per_column(self):
        built = build(
            tt(self.DF).fmt(
                where=cs.numeric() > 100,
                fn=lambda values: [f"selected:{value}" for value in values],
            ),
            "typst",
        )

        assert built.data_body == [
            ["A", "selected:150.25", "20.5"],
            ["B", "80.75", "selected:200.75"],
        ]

    def test_where_uses_source_names_after_display_rename(self):
        built = build(
            tt(self.DF)
            .set_name(j="Price", name="Unit price")
            .fmt(j="Price", where=pl.col("Price") > 100, digits=0),
            "typst",
        )

        assert built.colnames_display == ["Product", "Unit price", "Stock"]
        assert built.data_body[0] == ["A", "150", "20.5"]
        assert built.data_body[1] == ["B", "80.75", "200.75"]

    def test_where_maps_rows_past_row_groups(self):
        built = build(
            tt(self.DF).group(i={"Second": 1}).fmt(where=cs.numeric() > 100, digits=0),
            "typst",
        )

        assert built.data_body == [
            ["A", "150", "20.5"],
            ["Second", "", ""],
            ["B", "80.75", "201"],
        ]


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
            ("a&b", "typst", "ascii", "a&b"),
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


class TestLinebreak:
    def test_typst_uses_native_linebreak_and_escapes_text(self):
        df = pl.DataFrame({"text": ["first\n#second"]})
        out = tt(df).theme_plain().fmt(j="text", linebreak="\n").render("typst")
        assert "[first \\ \\#second]" in out

    def test_html_uses_br_and_escapes_text(self):
        df = pl.DataFrame({"text": ["<first>|second&"]})
        out = tt(df).theme_plain().fmt(j="text", linebreak="|").render("html")
        assert "&lt;first&gt;<br>second&amp;" in out

    def test_escape_false_preserves_raw_text_around_html_break(self):
        df = pl.DataFrame({"text": ["<b>first</b>|second"]})
        out = tt(df, escape=False).theme_plain().fmt(j="text", linebreak="|").render("html")
        assert "<b>first</b><br>second" in out

    def test_directive_escape_escapes_chunks(self):
        df = pl.DataFrame({"text": ["#first|[second]"]})
        out = (
            tt(df, escape=False)
            .theme_plain()
            .fmt(j="text", linebreak="|", escape=True)
            .render("typst")
        )
        assert "[\\#first \\ \\[second\\]]" in out

    def test_ascii_leaves_marker_intact(self):
        df = pl.DataFrame({"text": ["first|second"]})
        out = tt(df).theme_plain().fmt(j="text", linebreak="|").render("ascii")
        assert "first|second" in out

    def test_linebreak_can_target_header(self):
        df = pl.DataFrame({"first|second": [1]})
        out = tt(df).theme_plain().fmt(i="header", linebreak="|").render("html")
        assert ">first<br>second</th>" in out

    def test_absent_marker_does_not_make_cell_trusted(self):
        df = pl.DataFrame({"text": ["#value"]})
        out = tt(df).theme_plain().fmt(j="text", linebreak="|").render("typst")
        assert "[\\#value]" in out

    def test_empty_marker_raises(self):
        df = pl.DataFrame({"text": ["value"]})
        with pytest.raises(ValueError, match="must not be empty"):
            tt(df).fmt(linebreak="")

    def test_non_string_marker_raises(self):
        df = pl.DataFrame({"text": ["value"]})
        with pytest.raises(TypeError, match="must be a string or None"):
            tt(df).fmt(linebreak=1)  # type: ignore[arg-type]


class TestMath:
    def test_typst_wraps_equation_without_escaping_math_syntax(self):
        df = pl.DataFrame({"equation": ["sum_(i=1)^n i"]})
        out = tt(df).theme_plain().fmt(j="equation", math=True).render("typst")
        assert "[$sum_(i=1)^n i$]" in out

    def test_existing_math_is_not_double_wrapped(self):
        df = pl.DataFrame({"equation": ["$x^2$"]})
        out = tt(df).theme_plain().fmt(j="equation", math=True).render("typst")
        assert "[$x^2$]" in out
        assert "[$$x^2$$]" not in out

    def test_scientific_math_is_not_double_wrapped(self):
        df = pl.DataFrame({"value": [1200.0]})
        out = (
            tt(df)
            .theme_plain()
            .fmt(j="value", digits=1, num_fmt="scientific", math=True)
            .render("typst")
        )
        assert "[$1.2 times 10^3$]" in out

    @pytest.mark.parametrize("output", ["html", "ascii"])
    def test_other_backends_retain_original_value(self, output):
        df = pl.DataFrame({"equation": ["x^2"]})
        out = tt(df).theme_plain().fmt(j="equation", math=True).render(output)
        assert "x^2" in out
        assert "$x^2$" not in out

    def test_math_and_linebreak_compose(self):
        df = pl.DataFrame({"equation": ["x = 1|y = 2"]})
        out = tt(df).theme_plain().fmt(j="equation", linebreak="|", math=True).render("typst")
        assert "[$x = 1 \\ y = 2$]" in out

    def test_non_bool_math_raises(self):
        df = pl.DataFrame({"equation": ["x"]})
        with pytest.raises(TypeError, match="math must be a bool"):
            tt(df).fmt(math="yes")  # type: ignore[arg-type]

    @pytest.mark.parametrize("escape", [0, 1, "yes", None])
    def test_escape_requires_bool(self, escape):
        with pytest.raises(TypeError, match="escape must be a bool"):
            tt(pl.DataFrame({"x": [1]})).fmt(escape=escape)


@pytest.mark.typst
class TestFn:
    def test_fn_must_be_callable(self):
        with pytest.raises(TypeError, match="fn must be callable"):
            tt(pl.DataFrame({"x": [1]})).fmt(fn="upper")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("result", "type_name"),
        [
            ("abc", "str"),
            ((value for value in ["a", "b", "c"]), "generator"),
        ],
    )
    def test_fn_must_return_non_string_sequence(self, result, type_name):
        table = tt(pl.DataFrame({"x": [1, 2, 3]})).fmt(fn=lambda _values: result)

        with pytest.raises(TypeError, match=rf"non-string sequence, got {type_name}"):
            table.render("typst")

    def test_empty_row_selector_does_not_fall_back_to_body(self):
        df = pl.DataFrame({"value": [1, 2]})
        out = tt(df).theme_plain().fmt(i=[], fn=lambda vec: ["changed"] * len(vec)).render("typst")
        assert "changed" not in out
        assert "[1]" in out
        assert "[2]" in out

    def test_fn_column_transform(self):
        df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
        out = tt(df).fmt(j="x", fn=lambda vec: [f"#{v}" for v in vec]).render("typst")
        assert "\\#1" in out
        assert "\\#2" in out
        assert "\\#3" in out

    def test_fn_receives_typed_values_by_default(self):
        df = pl.DataFrame({"x": [1.25, None, 3.5]})
        seen = []

        def format_typed(values):
            seen.extend(values)
            return ["missing" if value is None else f"{value * 2:.1f}" for value in values]

        out = tt(df).fmt(j="x", fn=format_typed).render("typst")

        assert seen == [1.25, None, 3.5]
        assert "2.5" in out
        assert "missing" in out
        assert "7.0" in out

    def test_fn_values_rejects_unknown_value(self):
        with pytest.raises(ValueError, match="fn_values must be either"):
            tt(pl.DataFrame({"x": [1]})).fmt(fn=lambda values: values, fn_values="raw")

    def test_default_typed_fn_values_cannot_be_combined_with_digits(self):
        with pytest.raises(ValueError, match="digits cannot be combined"):
            tt(pl.DataFrame({"x": [1.25]})).fmt(
                digits=2,
                fn=lambda values: values,
            )

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
        out = tt(df).theme_plain().fmt(i="header", fn=lambda vec: ["renamed"]).render("typst")
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
        out = (
            tt(df)
            .fmt(
                j="v",
                digits=2,
                fn=lambda vec: [f"{v}x" for v in vec],
                fn_values="display",
            )
            .render("typst")
        )
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
            .fmt(j="v", fn=lambda vec: [f"[{v}]" for v in vec], fn_values="display")
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
