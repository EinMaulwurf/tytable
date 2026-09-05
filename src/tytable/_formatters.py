"""Reusable semantic value formatters for :meth:`tytable.TyTable.fmt`."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import time as Time
from datetime import timedelta as TimeDelta
from datetime import tzinfo as TzInfo
from decimal import (
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
    InvalidOperation,
    localcontext,
)
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

__all__ = ["currency", "date", "duration", "number", "percent", "unit"]

_LocaleName = Literal["de", "de-DE", "de_DE", "en", "en-US", "en_US"]
_LOCALES: dict[str, tuple[str, str]] = {
    "de": (",", "."),
    "de-DE": (",", "."),
    "de_DE": (",", "."),
    "en": (".", ","),
    "en-US": (".", ","),
    "en_US": (".", ","),
}
_CURRENCY_SYMBOLS = {"EUR": "€", "GBP": "£", "JPY": "¥", "USD": "$"}
_CURRENCY_MINOR_DIGITS = {
    "BHD": 3,
    "CLP": 0,
    "IQD": 3,
    "JPY": 0,
    "JOD": 3,
    "KRW": 0,
    "KWD": 3,
    "OMR": 3,
    "TND": 3,
}
_ROUNDING_MODES = {
    "ceiling": ROUND_CEILING,
    "down": ROUND_DOWN,
    "floor": ROUND_FLOOR,
    "half_down": ROUND_HALF_DOWN,
    "half_even": ROUND_HALF_EVEN,
    "half_up": ROUND_HALF_UP,
    "up": ROUND_UP,
}
_DEFAULT_COMPACT_LABELS = {3: "K", 6: "M", 9: "B", 12: "T"}
_DURATION_FACTORS = {
    "nanoseconds": Decimal("1e-9"),
    "microseconds": Decimal("1e-6"),
    "milliseconds": Decimal("1e-3"),
    "seconds": Decimal(1),
    "minutes": Decimal(60),
    "hours": Decimal(3600),
    "days": Decimal(86400),
}
_SI_PREFIXES = (
    (Decimal("1e24"), "Y"),
    (Decimal("1e21"), "Z"),
    (Decimal("1e18"), "E"),
    (Decimal("1e15"), "P"),
    (Decimal("1e12"), "T"),
    (Decimal("1e9"), "G"),
    (Decimal("1e6"), "M"),
    (Decimal("1e3"), "k"),
    (Decimal("1"), ""),
    (Decimal("1e-3"), "m"),
    (Decimal("1e-6"), "µ"),
    (Decimal("1e-9"), "n"),
    (Decimal("1e-12"), "p"),
    (Decimal("1e-15"), "f"),
    (Decimal("1e-18"), "a"),
    (Decimal("1e-21"), "z"),
    (Decimal("1e-24"), "y"),
)
_IEC_PREFIXES = tuple(
    (Decimal(1024) ** power, label)
    for power, label in reversed(
        (
            (1, "Ki"),
            (2, "Mi"),
            (3, "Gi"),
            (4, "Ti"),
            (5, "Pi"),
            (6, "Ei"),
            (7, "Zi"),
            (8, "Yi"),
        )
    )
)

_Notation = Literal["fixed", "significant", "scientific", "engineering", "compact"]
_Rounding = Literal[
    "half_even",
    "half_up",
    "half_down",
    "up",
    "down",
    "ceiling",
    "floor",
]


def _separators(
    locale: _LocaleName | None,
    decimal_mark: str | None,
    thousands_mark: str | None,
) -> tuple[str, str]:
    if locale is not None and not isinstance(locale, str):
        raise TypeError("locale must be a string or None")
    if locale is not None and locale not in _LOCALES:
        choices = ", ".join(repr(name) for name in ("de_DE", "en_US"))
        raise ValueError(f"locale must be one of the supported German or English names ({choices})")
    locale_decimal, locale_thousands = _LOCALES.get(locale or "en_US", (".", ","))
    decimal = locale_decimal if decimal_mark is None else decimal_mark
    thousands = locale_thousands if thousands_mark is None else thousands_mark
    if not isinstance(decimal, str) or not isinstance(thousands, str):
        raise TypeError("decimal_mark and thousands_mark must be strings")
    if decimal == thousands and decimal:
        raise ValueError("decimal_mark and thousands_mark must differ")
    return decimal, thousands


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise TypeError(f"semantic number formatter requires numeric values, got {value!r}")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"cannot format numeric value {value!r}") from exc


def _scale_factor(scale: object) -> Decimal:
    if isinstance(scale, bool) or not isinstance(scale, int | float | Decimal):
        raise TypeError("scale must be numeric")
    return Decimal(str(scale))


def _operation_precision(*values: Decimal, extra: int = 16) -> int:
    """Return enough precision for exact intermediate Decimal arithmetic."""
    significant_digits = sum(max(len(value.as_tuple().digits), 1) for value in values)
    return max(28, significant_digits + extra)


def _validate_precision(digits: object, min_digits: object) -> tuple[int, int]:
    if isinstance(digits, bool) or not isinstance(digits, int):
        raise TypeError("digits must be a non-negative integer")
    if digits < 0:
        raise ValueError("digits must be non-negative")
    if min_digits is None:
        return digits, digits
    if isinstance(min_digits, bool) or not isinstance(min_digits, int):
        raise TypeError("min_digits must be a non-negative integer or None")
    if min_digits < 0:
        raise ValueError("min_digits must be non-negative")
    if min_digits > digits:
        raise ValueError("min_digits must not exceed digits")
    return digits, min_digits


def _rounding_mode(rounding: object) -> str:
    if not isinstance(rounding, str):
        raise TypeError("rounding must be a string")
    if rounding not in _ROUNDING_MODES:
        choices = ", ".join(repr(name) for name in _ROUNDING_MODES)
        raise ValueError(f"rounding must be one of {choices}")
    return _ROUNDING_MODES[rounding]


def _magnitude_rounding(rounding: str, negative: bool) -> str:
    if not negative:
        return rounding
    if rounding == ROUND_FLOOR:
        return ROUND_CEILING
    if rounding == ROUND_CEILING:
        return ROUND_FLOOR
    return rounding


def _round_fixed(value: Decimal, digits: int, rounding: str) -> Decimal:
    quantum = Decimal(1).scaleb(-digits)
    precision = max(28, len(value.as_tuple().digits) + abs(value.adjusted()) + digits + 4)
    with localcontext() as context:
        context.prec = precision
        return value.quantize(quantum, rounding=rounding)


def _round_significant(value: Decimal, digits: int, rounding: str) -> Decimal:
    if not value:
        return value
    quantum = Decimal(1).scaleb(value.adjusted() - digits + 1)
    precision = max(28, len(value.as_tuple().digits) + abs(value.adjusted()) + digits + 4)
    with localcontext() as context:
        context.prec = precision
        return value.quantize(quantum, rounding=rounding)


def _localize_fixed(
    value: Decimal,
    *,
    digits: int,
    min_digits: int,
    decimal_mark: str,
    thousands_mark: str,
    grouping: bool,
) -> str:
    grouping_spec = "," if grouping else ""
    rendered = f"{value:{grouping_spec}.{digits}f}"
    integer, dot, fraction = rendered.partition(".")
    if digits > min_digits:
        fraction = fraction.rstrip("0")
        if len(fraction) < min_digits:
            fraction += "0" * (min_digits - len(fraction))
    if thousands_mark != ",":
        integer = integer.replace(",", thousands_mark)
    return integer + (decimal_mark + fraction if dot and fraction else "")


def _compact_thresholds(labels: Mapping[int, str] | None) -> list[tuple[Decimal, str]]:
    raw = _DEFAULT_COMPACT_LABELS if labels is None else labels
    if not isinstance(raw, Mapping):
        raise TypeError("compact_labels must be a mapping or None")
    result: list[tuple[Decimal, str]] = []
    for power, label in raw.items():
        if isinstance(power, bool) or not isinstance(power, int) or power <= 0:
            raise ValueError("compact label powers must be positive integers")
        if not isinstance(label, str):
            raise TypeError("compact labels must be strings")
        result.append((Decimal(10) ** power, label))
    return sorted(result, reverse=True)


def _scaled_with_prefix(
    magnitude: Decimal,
    thresholds: Sequence[tuple[Decimal, str]],
    *,
    digits: int,
    rounding: str,
) -> tuple[Decimal, str]:
    for index, (threshold, label) in enumerate(thresholds):
        if magnitude < threshold:
            continue
        scaled = magnitude / threshold
        if index > 0:
            higher_threshold, higher_label = thresholds[index - 1]
            if _round_fixed(scaled, digits, rounding) >= higher_threshold / threshold:
                return magnitude / higher_threshold, higher_label
        return scaled, label
    return magnitude, ""


def _format_finite_number(
    numeric: Decimal,
    *,
    digits: int,
    min_digits: int,
    decimal_mark: str,
    thousands_mark: str,
    grouping: bool,
    accounting: bool,
    notation: _Notation,
    rounding: str,
    normalize_negative_zero: bool,
    compact_thresholds: Sequence[tuple[Decimal, str]],
) -> str:
    with localcontext() as context:
        context.prec = _operation_precision(numeric, extra=digits + 16)
        return _format_finite_number_inner(
            numeric,
            digits=digits,
            min_digits=min_digits,
            decimal_mark=decimal_mark,
            thousands_mark=thousands_mark,
            grouping=grouping,
            accounting=accounting,
            notation=notation,
            rounding=rounding,
            normalize_negative_zero=normalize_negative_zero,
            compact_thresholds=compact_thresholds,
        )


def _format_finite_number_inner(
    numeric: Decimal,
    *,
    digits: int,
    min_digits: int,
    decimal_mark: str,
    thousands_mark: str,
    grouping: bool,
    accounting: bool,
    notation: _Notation,
    rounding: str,
    normalize_negative_zero: bool,
    compact_thresholds: Sequence[tuple[Decimal, str]],
) -> str:
    negative = numeric.is_signed()
    rounding = _magnitude_rounding(rounding, negative)
    magnitude = abs(numeric)
    notation_suffix = ""

    if notation == "compact":
        magnitude, notation_suffix = _scaled_with_prefix(
            magnitude, compact_thresholds, digits=digits, rounding=rounding
        )

    if notation == "significant":
        rounded = _round_significant(magnitude, digits, rounding)
        decimal_places = max(digits - rounded.adjusted() - 1, 0) if rounded else max(digits - 1, 0)
        rendered = _localize_fixed(
            rounded,
            digits=decimal_places,
            min_digits=decimal_places,
            decimal_mark=decimal_mark,
            thousands_mark=thousands_mark,
            grouping=grouping,
        )
    elif notation in {"scientific", "engineering"}:
        exponent_step = 3 if notation == "engineering" else 1
        exponent = (magnitude.adjusted() // exponent_step) * exponent_step if magnitude else 0
        mantissa = magnitude.scaleb(-exponent)
        rounded = _round_fixed(mantissa, digits, rounding)
        limit = Decimal(1000 if notation == "engineering" else 10)
        if rounded >= limit:
            exponent += exponent_step
            rounded = _round_fixed(magnitude.scaleb(-exponent), digits, rounding)
        rendered_mantissa = _localize_fixed(
            rounded,
            digits=digits,
            min_digits=min_digits,
            decimal_mark=decimal_mark,
            thousands_mark="",
            grouping=False,
        )
        rendered = f"{rendered_mantissa}e{exponent:+d}"
    else:
        rounded = _round_fixed(magnitude, digits, rounding)
        rendered = _localize_fixed(
            rounded,
            digits=digits,
            min_digits=min_digits,
            decimal_mark=decimal_mark,
            thousands_mark=thousands_mark,
            grouping=grouping,
        )

    if normalize_negative_zero and not rounded:
        negative = False
    rendered += notation_suffix
    if negative:
        return f"({rendered})" if accounting else f"-{rendered}"
    return rendered


def number(
    *,
    digits: int = 2,
    min_digits: int | None = None,
    notation: _Notation = "fixed",
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    accounting: bool = False,
    compact: bool = False,
    compact_labels: Mapping[int, str] | None = None,
    scale: int | float | Decimal = 1,
    rounding: _Rounding = "half_even",
    normalize_negative_zero: bool = True,
    prefix: str = "",
    suffix: str = "",
    null: str = "—",
    nan: str | None = None,
    inf: str = "infinity",
    negative_inf: str = "-infinity",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a locale-aware number formatter.

    ``locale="de_DE"`` uses a decimal comma and period grouping, producing
    values such as ``"1.023,87"``. The supported locale names are deliberately
    small separator presets rather than a complete CLDR implementation. Use
    ``decimal_mark`` and ``thousands_mark`` for other conventions. The formatter
    multiplies values by ``scale`` before formatting. ``min_digits`` permits
    variable decimal places. ``notation`` selects fixed, significant, scientific,
    engineering, or compact output.
    """
    digits, resolved_min_digits = _validate_precision(digits, min_digits)
    for name, value in (
        ("grouping", grouping),
        ("accounting", accounting),
        ("compact", compact),
        ("normalize_negative_zero", normalize_negative_zero),
    ):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be a bool")
    if not isinstance(notation, str):
        raise TypeError("notation must be a string")
    if notation not in {"fixed", "significant", "scientific", "engineering", "compact"}:
        raise ValueError(
            "notation must be 'fixed', 'significant', 'scientific', 'engineering', or 'compact'"
        )
    if compact and notation not in {"fixed", "compact"}:
        raise ValueError("compact=True cannot be combined with another notation")
    if compact:
        notation = "compact"
    if notation == "significant" and digits == 0:
        raise ValueError("digits must be positive for significant notation")
    if not all(isinstance(value, str) for value in (prefix, suffix, null, inf, negative_inf)):
        raise TypeError("prefix, suffix, null, inf, and negative_inf must be strings")
    if nan is not None and not isinstance(nan, str):
        raise TypeError("nan must be a string or None")
    decimal, thousands = _separators(locale, decimal_mark, thousands_mark)
    scale_factor = _scale_factor(scale)
    rounding_mode = _rounding_mode(rounding)
    thresholds = _compact_thresholds(compact_labels)

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None:
                result.append(null)
                continue
            raw_numeric = _decimal(value)
            with localcontext() as context:
                context.prec = _operation_precision(raw_numeric, scale_factor)
                numeric = raw_numeric * scale_factor
            if numeric.is_nan():
                result.append(null if nan is None else f"{prefix}{nan}{suffix}")
                continue
            if numeric.is_infinite():
                special = negative_inf if numeric.is_signed() else inf
                result.append(f"{prefix}{special}{suffix}")
                continue
            formatted = _format_finite_number(
                numeric,
                digits=digits,
                min_digits=resolved_min_digits,
                decimal_mark=decimal,
                thousands_mark=thousands,
                grouping=grouping,
                accounting=accounting,
                notation=notation,
                rounding=rounding_mode,
                normalize_negative_zero=normalize_negative_zero,
                compact_thresholds=thresholds,
            )
            if accounting and formatted.startswith("(") and formatted.endswith(")"):
                result.append(f"({prefix}{formatted[1:-1]}{suffix})")
            else:
                result.append(f"{prefix}{formatted}{suffix}")
        return result

    return formatter


def currency(
    code: str = "EUR",
    *,
    digits: int | None = 2,
    min_digits: int | None = None,
    notation: _Notation = "fixed",
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    symbol: str | None = None,
    symbol_position: Literal["auto", "prefix", "suffix"] = "auto",
    accounting: bool = False,
    compact: bool = False,
    compact_labels: Mapping[int, str] | None = None,
    scale: int | float | Decimal = 1,
    rounding: _Rounding = "half_even",
    normalize_negative_zero: bool = True,
    null: str = "—",
    nan: str | None = None,
    inf: str = "infinity",
    negative_inf: str = "-infinity",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a currency formatter with numeric and symbol-placement options.

    Set ``digits=None`` to use known currency digits. The default remains two
    digits for compatibility.
    """
    if not isinstance(code, str):
        raise TypeError("currency code must be a string")
    if not code:
        raise ValueError("currency code must be a non-empty string")
    normalized_code = code.upper()
    currency_symbol = symbol if symbol is not None else _CURRENCY_SYMBOLS.get(normalized_code, code)
    if not isinstance(currency_symbol, str):
        raise TypeError("symbol must be a string or None")
    if not isinstance(symbol_position, str):
        raise TypeError("symbol_position must be a string")
    if symbol_position not in {"auto", "prefix", "suffix"}:
        raise ValueError("symbol_position must be 'auto', 'prefix', or 'suffix'")
    resolved_digits = _CURRENCY_MINOR_DIGITS.get(normalized_code, 2) if digits is None else digits
    suffix_symbol = symbol_position == "suffix" or (
        symbol_position == "auto" and locale in {"de", "de-DE", "de_DE"}
    )
    return number(
        digits=resolved_digits,
        min_digits=min_digits,
        notation=notation,
        locale=locale,
        decimal_mark=decimal_mark,
        thousands_mark=thousands_mark,
        grouping=grouping,
        accounting=accounting,
        compact=compact,
        compact_labels=compact_labels,
        scale=scale,
        rounding=rounding,
        normalize_negative_zero=normalize_negative_zero,
        prefix="" if suffix_symbol else currency_symbol,
        suffix=f" {currency_symbol}" if suffix_symbol else "",
        null=null,
        nan=nan,
        inf=inf,
        negative_inf=negative_inf,
    )


def percent(
    *,
    digits: int = 1,
    min_digits: int | None = None,
    notation: _Notation = "fixed",
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    accounting: bool = False,
    scale: int | float | Decimal = 100,
    rounding: _Rounding = "half_even",
    normalize_negative_zero: bool = True,
    null: str = "—",
    nan: str | None = None,
    inf: str = "infinity",
    negative_inf: str = "-infinity",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a percentage formatter.

    The default ``scale=100`` converts fractions to percentages.
    """
    return number(
        digits=digits,
        min_digits=min_digits,
        notation=notation,
        locale=locale,
        decimal_mark=decimal_mark,
        thousands_mark=thousands_mark,
        grouping=grouping,
        accounting=accounting,
        scale=scale,
        rounding=rounding,
        normalize_negative_zero=normalize_negative_zero,
        suffix=" %" if locale in {"de", "de-DE", "de_DE"} else "%",
        null=null,
        nan=nan,
        inf=inf,
        negative_inf=negative_inf,
    )


def date(
    pattern: str = "%Y-%m-%d",
    *,
    timezone: str | TzInfo | None = None,
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a formatter for Python date, datetime, and time values.

    ``timezone`` converts timezone-aware datetimes before formatting.
    """
    if not isinstance(pattern, str):
        raise TypeError("date pattern must be a string")
    if not pattern:
        raise ValueError("date pattern must be a non-empty string")
    if not isinstance(null, str):
        raise TypeError("null must be a string")
    target_timezone: TzInfo | None
    if isinstance(timezone, str):
        try:
            target_timezone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone {timezone!r}") from exc
    elif timezone is None or isinstance(timezone, TzInfo):
        target_timezone = timezone
    else:
        raise TypeError("timezone must be an IANA name, tzinfo object, or None")

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None:
                result.append(null)
            elif isinstance(value, DateTime):
                if target_timezone is not None:
                    if value.tzinfo is None or value.utcoffset() is None:
                        raise ValueError("timezone conversion requires timezone-aware datetimes")
                    value = value.astimezone(target_timezone)
                result.append(value.strftime(pattern))
            elif isinstance(value, Time):
                if target_timezone is not None:
                    raise ValueError("timezone conversion does not support time-only values")
                result.append(value.strftime(pattern))
            elif isinstance(value, Date):
                result.append(value.strftime(pattern))
            else:
                raise TypeError(f"date formatter requires date/time values, got {value!r}")
        return result

    return formatter


def duration(
    *,
    input_unit: Literal[
        "nanoseconds", "microseconds", "milliseconds", "seconds", "minutes", "hours", "days"
    ] = "seconds",
    digits: int = 0,
    min_digits: int | None = None,
    style: Literal["clock", "human"] = "clock",
    rounding: _Rounding = "half_even",
    normalize_negative_zero: bool = True,
    null: str = "—",
    nan: str | None = None,
    inf: str = "infinity",
    negative_inf: str = "-infinity",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a clock-style formatter for numeric durations or ``timedelta`` values.

    Numeric values use ``input_unit``. Clock output uses ``HH:MM:SS`` and permits
    more than 24 hours. Human output uses labeled day, hour, minute, and second
    fields.
    """
    if not isinstance(input_unit, str):
        raise TypeError("input_unit must be a string")
    if input_unit not in _DURATION_FACTORS:
        choices = ", ".join(repr(name) for name in _DURATION_FACTORS)
        raise ValueError(f"input_unit must be one of {choices}")
    digits, resolved_min_digits = _validate_precision(digits, min_digits)
    if not isinstance(style, str):
        raise TypeError("style must be a string")
    if style not in {"clock", "human"}:
        raise ValueError("style must be 'clock' or 'human'")
    if not isinstance(normalize_negative_zero, bool):
        raise TypeError("normalize_negative_zero must be a bool")
    if not all(isinstance(value, str) for value in (null, inf, negative_inf)):
        raise TypeError("null, inf, and negative_inf must be strings")
    if nan is not None and not isinstance(nan, str):
        raise TypeError("nan must be a string or None")

    factor = _DURATION_FACTORS[input_unit]
    rounding_mode = _rounding_mode(rounding)

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None:
                result.append(null)
                continue
            if isinstance(value, TimeDelta):
                seconds = Decimal(value.days * 86400 + value.seconds) + Decimal(
                    value.microseconds
                ) / Decimal(1_000_000)
            else:
                raw_seconds = _decimal(value)
                with localcontext() as context:
                    context.prec = _operation_precision(raw_seconds, factor)
                    seconds = raw_seconds * factor
            if seconds.is_nan():
                result.append(null if nan is None else nan)
                continue
            if seconds.is_infinite():
                result.append(negative_inf if seconds.is_signed() else inf)
                continue
            magnitude_rounding = _magnitude_rounding(rounding_mode, seconds.is_signed())
            rounded = _round_fixed(abs(seconds), digits, magnitude_rounding)
            negative = seconds.is_signed() and not (normalize_negative_zero and not rounded)
            sign = "-" if negative else ""
            magnitude = abs(rounded)
            if style == "human":
                days, remainder = divmod(magnitude, Decimal(86400))
                hours, remainder = divmod(remainder, Decimal(3600))
                minutes, seconds_part = divmod(remainder, Decimal(60))
                parts: list[str] = []
                for amount, label in ((days, "d"), (hours, "h"), (minutes, "m")):
                    if amount:
                        parts.append(f"{int(amount)}{label}")
                if seconds_part or not parts:
                    rendered_seconds = _localize_fixed(
                        seconds_part,
                        digits=digits,
                        min_digits=resolved_min_digits,
                        decimal_mark=".",
                        thousands_mark="",
                        grouping=False,
                    )
                    parts.append(f"{rendered_seconds}s")
                result.append(f"{sign}{' '.join(parts)}")
                continue
            hours, remainder = divmod(magnitude, Decimal(3600))
            minutes, seconds_part = divmod(remainder, Decimal(60))
            rendered_seconds = _localize_fixed(
                seconds_part,
                digits=digits,
                min_digits=resolved_min_digits,
                decimal_mark=".",
                thousands_mark="",
                grouping=False,
            )
            seconds_width = 2 + (
                1 + len(rendered_seconds.partition(".")[2]) if "." in rendered_seconds else 0
            )
            result.append(
                f"{sign}{int(hours):02d}:{int(minutes):02d}:{rendered_seconds:0>{seconds_width}}"
            )
        return result

    return formatter


def unit(
    symbol: str,
    *,
    digits: int = 2,
    min_digits: int | None = None,
    notation: _Notation = "fixed",
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    accounting: bool = False,
    si_prefix: bool = False,
    iec_prefix: bool = False,
    compact: bool = False,
    compact_labels: Mapping[int, str] | None = None,
    scale: int | float | Decimal = 1,
    rounding: _Rounding = "half_even",
    normalize_negative_zero: bool = True,
    space: str = " ",
    null: str = "—",
    nan: str | None = None,
    inf: str = "infinity",
    negative_inf: str = "-infinity",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a number formatter that appends a unit symbol.

    The formatter multiplies values by ``scale`` first. Set ``si_prefix=True``
    to select an SI prefix. Set ``iec_prefix=True`` to select an IEC binary
    prefix.
    """
    if not isinstance(symbol, str):
        raise TypeError("unit symbol must be a string")
    if not symbol:
        raise ValueError("unit symbol must be a non-empty string")
    if not isinstance(si_prefix, bool):
        raise TypeError("si_prefix must be a bool")
    if not isinstance(iec_prefix, bool):
        raise TypeError("iec_prefix must be a bool")
    if si_prefix and iec_prefix:
        raise ValueError("si_prefix and iec_prefix cannot both be true")
    if (si_prefix or iec_prefix) and (compact or notation == "compact"):
        raise ValueError("unit prefixes cannot be combined with compact notation")
    if not isinstance(space, str):
        raise TypeError("space must be a string")
    scale_factor = _scale_factor(scale)
    rounding_mode = _rounding_mode(rounding)

    # Construct once to share number's validation and locale conventions.
    plain = number(
        digits=digits,
        min_digits=min_digits,
        notation=notation,
        locale=locale,
        decimal_mark=decimal_mark,
        thousands_mark=thousands_mark,
        grouping=grouping,
        accounting=accounting,
        compact=compact,
        compact_labels=compact_labels,
        rounding=rounding,
        normalize_negative_zero=normalize_negative_zero,
        null=null,
        nan=nan,
        inf=inf,
        negative_inf=negative_inf,
    )

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None:
                result.append(null)
                continue
            raw_numeric = _decimal(value)
            with localcontext() as context:
                context.prec = _operation_precision(raw_numeric, scale_factor)
                numeric = raw_numeric * scale_factor
            scaled = numeric
            prefix = ""
            magnitude = abs(numeric)
            prefix_table = _SI_PREFIXES if si_prefix else _IEC_PREFIXES if iec_prefix else ()
            if prefix_table and numeric.is_finite() and magnitude:
                with localcontext() as context:
                    context.prec = _operation_precision(magnitude, extra=digits + 16)
                    scaled_magnitude, prefix = _scaled_with_prefix(
                        magnitude,
                        prefix_table,
                        digits=digits,
                        rounding=_magnitude_rounding(rounding_mode, numeric.is_signed()),
                    )
                scaled = scaled_magnitude.copy_negate() if numeric.is_signed() else scaled_magnitude
            rendered = plain([scaled])[0]
            if numeric.is_nan() and nan is None:
                result.append(rendered)
                continue
            suffix = f"{space}{prefix}{symbol}"
            if accounting and rendered.startswith("(") and rendered.endswith(")"):
                result.append(f"({rendered[1:-1]}{suffix})")
            else:
                result.append(f"{rendered}{suffix}")
        return result

    return formatter
