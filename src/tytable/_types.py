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


@dataclass(frozen=True, slots=True)
class _ColGroupSelector:
    """Select source columns belonging to a registered column group."""

    label: str
    level: int


def regex(pattern: str) -> _RegexSelector:
    """Select source columns matched by a Python ``re.search`` pattern.

    Invalid patterns, patterns longer than 500 characters, and patterns that
    match no source columns raise :class:`ValueError` when resolved.
    """
    if not isinstance(pattern, str):
        raise TypeError(f"regex pattern must be a string, got {type(pattern).__name__}")
    return _RegexSelector(pattern=pattern)


def _normalize_group_label(name: str, label: object) -> str:
    """Normalize one public semantic group label to its displayed string."""
    if label is None:
        raise ValueError(f"{name} label must not be None")
    normalized = str(label)
    if not normalized.strip():
        raise ValueError(f"{name} label must not be empty")
    return normalized


def colgroup(*, label: object, level: int) -> _ColGroupSelector:
    """Select source columns in groups with an exact label at one level.

    Level zero is the first-created, innermost grouping level. Every group
    with the requested nonempty label at that level contributes its member
    columns.
    """
    normalized_label = _normalize_group_label("colgroup", label)
    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError(f"colgroup level must be an integer, got {type(level).__name__}")
    if level < 0:
        raise ValueError(f"colgroup level must be non-negative, got {level}")
    return _ColGroupSelector(label=normalized_label, level=level)


_ColumnSelectorItem: TypeAlias = int | str | pl.Expr | _RegexSelector | _ColGroupSelector
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


@dataclass(frozen=True, slots=True)
class _RowGroupSelector:
    """Select source-data rows belonging to registered row groups."""

    label: str


def groupi(*, label: object | None = None) -> _GroupISelector:
    """Select row-group separator rows, optionally by exact registered label.

    Omitting ``label`` selects every row-group separator, like the ``"groupi"``
    string selector. When labels repeat, every exact match is selected.
    """
    normalized_label = None if label is None else _normalize_group_label("groupi", label)
    return _GroupISelector(label=normalized_label)


def rowgroup(*, label: object) -> _RowGroupSelector:
    """Select source-data rows belonging to every group with an exact label.

    Each matching run begins after its separator and ends before the next
    separator. Repeated labels combine their source-data rows.
    """
    return _RowGroupSelector(label=_normalize_group_label("rowgroup", label))


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


_RowSelectorItem: TypeAlias = int | str | _GroupISelector | _RowGroupSelector
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
