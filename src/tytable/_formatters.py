"""Reusable semantic value formatters for :meth:`tytable.TyTable.fmt`."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import time as Time
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

__all__ = ["currency", "date", "number", "percent"]

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
    prefix: str = "",
    suffix: str = "",
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a locale-aware number formatter.

    ``locale="de_DE"`` uses a decimal comma and period grouping, producing
    values such as ``"1.023,87"``. The supported locale names are deliberately
    small separator presets rather than a complete CLDR implementation; pass
    ``decimal_mark`` and ``thousands_mark`` for other conventions.
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

    def formatter(values: Sequence[Any]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                result.append(null)
                continue
            formatted = _format_number(
                value,
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
        prefix="" if german else currency_symbol,
        suffix=f" {currency_symbol}" if german else "",
        null=null,
    )


def percent(
    *,
    digits: int = 1,
    locale: _LocaleName | None = None,
    scale: float = 100,
    null: str = "—",
) -> Callable[[Sequence[Any]], list[str]]:
    """Create a percentage formatter; fractions are multiplied by ``scale``."""
    if isinstance(scale, bool) or not isinstance(scale, int | float | Decimal):
        raise TypeError("scale must be numeric")
    base = number(
        digits=digits,
        locale=locale,
        suffix=" %" if locale in {"de", "de-DE", "de_DE"} else "%",
        null=null,
    )

    def formatter(values: Sequence[Any]) -> list[str]:
        scaled = [
            value
            if value is None or (isinstance(value, float) and math.isnan(value))
            else _decimal(value) * Decimal(str(scale))
            for value in values
        ]
        return base(scaled)

    return formatter


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
