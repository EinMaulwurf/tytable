"""Public typing helpers for :mod:`tytable`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias, TypedDict

import polars as pl


@dataclass(frozen=True, slots=True)
class _RegexSelector:
    """Select source columns whose names match a Python regular expression."""

    pattern: str


def regex(pattern: str) -> _RegexSelector:
    """Select source columns matched by a Python ``re.search`` pattern.

    Invalid patterns, patterns longer than 500 characters, and patterns that
    match no source columns raise :class:`ValueError` when resolved.
    """
    if not isinstance(pattern, str):
        raise TypeError(f"regex pattern must be a string, got {type(pattern).__name__}")
    return _RegexSelector(pattern=pattern)


_ColumnSelectorItem: TypeAlias = int | str | pl.Expr | _RegexSelector
_ColumnSelectorSpec: TypeAlias = _ColumnSelectorItem | Sequence[_ColumnSelectorItem]
_ColumnSelector: TypeAlias = _ColumnSelectorSpec | None


@dataclass(frozen=True, slots=True)
class _GroupJSelector:
    """Select every column-group header row or one stable semantic level."""

    level: int | None = None


@dataclass(frozen=True, slots=True)
class _GroupISelector:
    """Select every row-group separator or those with one registered label."""

    label: str | None = None


def groupi(*, label: str | None = None) -> _GroupISelector:
    """Select row-group separator rows, optionally by exact registered label.

    Omitting ``label`` selects every row-group separator, like the ``"groupi"``
    string selector. When labels repeat, every exact match is selected.
    """
    if label is not None and not isinstance(label, str):
        raise TypeError(f"groupi label must be a string, got {type(label).__name__}")
    return _GroupISelector(label=label)


def groupj(*, level: int | None = None) -> _GroupJSelector:
    """Select column-group header rows, optionally at one nesting level.

    Level zero is the first-created, innermost grouping level nearest the
    ordinary column-name header. Later grouping levels increase outward.
    Omitting ``level`` selects every column-group header row, like the legacy
    ``"groupj"`` string selector.
    """
    if level is not None:
        if isinstance(level, bool) or not isinstance(level, int):
            raise TypeError(f"groupj level must be an integer, got {type(level).__name__}")
        if level < 0:
            raise ValueError(f"groupj level must be non-negative, got {level}")
    return _GroupJSelector(level=level)


_RowSelectorItem: TypeAlias = int | str | _GroupISelector
_RowSelector: TypeAlias = (
    _RowSelectorItem
    | Sequence[_RowSelectorItem]
    | pl.Expr
    | pl.Series
    | Callable[[dict], bool]
    | None
)
_StyleRowSelectorItem: TypeAlias = _RowSelectorItem | _GroupJSelector
_StyleRowSelector: TypeAlias = (
    _StyleRowSelectorItem
    | Sequence[_StyleRowSelectorItem]
    | pl.Expr
    | pl.Series
    | Callable[[dict], bool]
    | None
)


class NoteDict(TypedDict, total=False):
    """Dictionary form of a table note accepted by :func:`tytable.tt`.

    ``text`` is the footer text and ``marker`` is an optional explicit marker.
    ``i``, ``j``, and ``where`` use the same selector semantics as
    :meth:`tytable.TyTable.fmt`; when a target is present and ``marker`` is
    omitted, tytable assigns a number.
    """

    text: str
    marker: str | None
    i: _RowSelector
    j: _ColumnSelector
    where: pl.Expr | None
