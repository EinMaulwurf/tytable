"""Public typing helpers for :mod:`tytable`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias, TypedDict

import polars as pl

_ColumnSelectorItem: TypeAlias = int | str | pl.Expr
_ColumnSelectorSpec: TypeAlias = _ColumnSelectorItem | Sequence[_ColumnSelectorItem]
_ColumnSelector: TypeAlias = _ColumnSelectorSpec | None


@dataclass(frozen=True, slots=True)
class _GroupJSelector:
    """Select every column-group header row or one stable semantic level."""

    level: int | None = None


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


_StyleRowSelectorItem: TypeAlias = int | str | _GroupJSelector
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
    ``i``, ``j``, ``where``, and ``regex`` use the same selector semantics as
    :meth:`tytable.TyTable.fmt`; when a target is present and ``marker`` is
    omitted, tytable assigns a number.
    """

    text: str
    marker: str | None
    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None
    j: _ColumnSelector
    where: pl.Expr | None
    regex: bool
