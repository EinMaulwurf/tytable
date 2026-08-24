"""Reusable semantic value formatters for :meth:`tytable.TyTable.fmt`."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import time as Time
from datetime import timedelta as TimeDelta
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

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


def _separators(
    locale: _LocaleName | None,
    decimal_mark: str | None,
    thousands_mark: str | None,
) -> tuple[str, str]:
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


def _format_number(
    value: object,
    *,
    digits: int,
    decimal_mark: str,
    thousands_mark: str,
    grouping: bool,
    accounting: bool,
    compact: bool,
) -> str:
    numeric = _decimal(value)
    if not numeric.is_finite():
        return str(numeric).lower()

    negative = numeric < 0
    magnitude = abs(numeric)
    suffix = ""
    if compact:
        for threshold, label in (
            (Decimal("1e12"), "T"),
            (Decimal("1e9"), "B"),
            (Decimal("1e6"), "M"),
            (Decimal("1e3"), "K"),
        ):
            if magnitude >= threshold:
                magnitude /= threshold
                suffix = label
                break

    grouping_spec = "," if grouping else ""
    rendered = f"{magnitude:{grouping_spec}.{digits}f}"
    integer, dot, fraction = rendered.partition(".")
    if thousands_mark != ",":
        integer = integer.replace(",", thousands_mark)
    rendered = integer + (decimal_mark + fraction if dot and digits else "") + suffix
    if negative:
        return f"({rendered})" if accounting else f"-{rendered}"
    return rendered


def number(
    *,
    digits: int = 2,
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    accounting: bool = False,
    compact: bool = False,
    scale: int | float | Decimal = 1,
    prefix: str = "",
    suffix: str = "",
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a locale-aware number formatter.

    ``locale="de_DE"`` uses a decimal comma and period grouping, producing
    values such as ``"1.023,87"``. The supported locale names are deliberately
    small separator presets rather than a complete CLDR implementation. Use
    ``decimal_mark`` and ``thousands_mark`` for other conventions. The formatter
    multiplies values by ``scale`` before formatting.
    """
    if isinstance(digits, bool) or not isinstance(digits, int):
        raise TypeError("digits must be a non-negative integer")
    if digits < 0:
        raise ValueError("digits must be non-negative")
    for name, value in (
        ("grouping", grouping),
        ("accounting", accounting),
        ("compact", compact),
    ):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be a bool")
    if not all(isinstance(value, str) for value in (prefix, suffix, null)):
        raise TypeError("prefix, suffix, and null must be strings")
    decimal, thousands = _separators(locale, decimal_mark, thousands_mark)
    scale_factor = _scale_factor(scale)

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                result.append(null)
                continue
            formatted = _format_number(
                _decimal(value) * scale_factor,
                digits=digits,
                decimal_mark=decimal,
                thousands_mark=thousands,
                grouping=grouping,
                accounting=accounting,
                compact=compact,
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
    digits: int = 2,
    locale: _LocaleName | None = None,
    symbol: str | None = None,
    accounting: bool = False,
    scale: int | float | Decimal = 1,
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a currency formatter with locale-appropriate symbol placement."""
    if not isinstance(code, str) or not code:
        raise ValueError("currency code must be a non-empty string")
    currency_symbol = symbol if symbol is not None else _CURRENCY_SYMBOLS.get(code.upper(), code)
    if not isinstance(currency_symbol, str):
        raise TypeError("symbol must be a string or None")
    german = locale in {"de", "de-DE", "de_DE"}
    return number(
        digits=digits,
        locale=locale,
        accounting=accounting,
        scale=scale,
        prefix="" if german else currency_symbol,
        suffix=f" {currency_symbol}" if german else "",
        null=null,
    )


def percent(
    *,
    digits: int = 1,
    locale: _LocaleName | None = None,
    scale: int | float | Decimal = 100,
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a percentage formatter; fractions are multiplied by ``scale``."""
    return number(
        digits=digits,
        locale=locale,
        scale=scale,
        suffix=" %" if locale in {"de", "de-DE", "de_DE"} else "%",
        null=null,
    )


def date(
    pattern: str = "%Y-%m-%d",
    *,
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a formatter for Python date, datetime, and time values."""
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("date pattern must be a non-empty string")
    if not isinstance(null, str):
        raise TypeError("null must be a string")

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None:
                result.append(null)
            elif isinstance(value, Date | DateTime | Time):
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
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a clock-style formatter for numeric durations or ``timedelta`` values.

    Numeric values are interpreted in ``input_unit``. Output uses ``HH:MM:SS``;
    hours may exceed 24, and ``digits`` controls fractional-second places.
    """
    if input_unit not in _DURATION_FACTORS:
        choices = ", ".join(repr(name) for name in _DURATION_FACTORS)
        raise ValueError(f"input_unit must be one of {choices}")
    if isinstance(digits, bool) or not isinstance(digits, int):
        raise TypeError("digits must be a non-negative integer")
    if digits < 0:
        raise ValueError("digits must be non-negative")
    if not isinstance(null, str):
        raise TypeError("null must be a string")

    factor = _DURATION_FACTORS[input_unit]
    quantum = Decimal(1).scaleb(-digits)

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                result.append(null)
                continue
            if isinstance(value, TimeDelta):
                seconds = Decimal(value.days * 86400 + value.seconds) + Decimal(
                    value.microseconds
                ) / Decimal(1_000_000)
            else:
                seconds = _decimal(value) * factor
            if not seconds.is_finite():
                result.append(str(seconds).lower())
                continue
            rounded = seconds.quantize(quantum)
            sign = "-" if rounded < 0 else ""
            magnitude = abs(rounded)
            hours, remainder = divmod(magnitude, Decimal(3600))
            minutes, seconds_part = divmod(remainder, Decimal(60))
            seconds_width = 2 + (digits + 1 if digits else 0)
            result.append(
                f"{sign}{int(hours):02d}:{int(minutes):02d}:{seconds_part:0{seconds_width}.{digits}f}"
            )
        return result

    return formatter


def unit(
    symbol: str,
    *,
    digits: int = 2,
    locale: _LocaleName | None = None,
    decimal_mark: str | None = None,
    thousands_mark: str | None = None,
    grouping: bool = True,
    accounting: bool = False,
    si_prefix: bool = False,
    scale: int | float | Decimal = 1,
    space: str = " ",
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a number formatter that appends a unit symbol.

    The formatter multiplies values by ``scale`` first. Set ``si_prefix=True``
    to select an SI prefix from yocto (``y``) through yotta (``Y``).
    """
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("unit symbol must be a non-empty string")
    if not isinstance(si_prefix, bool):
        raise TypeError("si_prefix must be a bool")
    if not isinstance(space, str):
        raise TypeError("space must be a string")
    scale_factor = _scale_factor(scale)

    # Construct once to share number's validation and locale conventions.
    plain = number(
        digits=digits,
        locale=locale,
        decimal_mark=decimal_mark,
        thousands_mark=thousands_mark,
        grouping=grouping,
        accounting=accounting,
        null=null,
    )

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                result.append(null)
                continue
            numeric = _decimal(value) * scale_factor
            scaled = numeric
            prefix = ""
            magnitude = abs(numeric)
            if si_prefix and numeric.is_finite() and magnitude:
                for threshold, candidate in _SI_PREFIXES:
                    if magnitude >= threshold:
                        scaled = numeric / threshold
                        prefix = candidate
                        break
            rendered = plain([scaled])[0]
            suffix = f"{space}{prefix}{symbol}"
            if accounting and rendered.startswith("(") and rendered.endswith(")"):
                result.append(f"({rendered[1:-1]}{suffix})")
            else:
                result.append(f"{rendered}{suffix}")
        return result

    return formatter
