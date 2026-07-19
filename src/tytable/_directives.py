"""
Frozen dataclasses recording user *intent* (styles, formats, plots, groups).

These are produced by the chaining methods on :class:`~tytable._tytable.TyTable`
and replayed at render time by :func:`tytable._resolve.build`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass(frozen=True)
class StyleDirective:
    """A single ``.style()`` call: selectors plus the cell properties to apply."""

    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None
    j: int | str | Sequence[int | str] | None
    where: pl.Expr | None = None
    regex: bool = False
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikeout: bool | None = None
    monospace: bool | None = None
    smallcaps: bool | None = None
    color: str | None = None
    background: str | None = None
    fontsize: float | None = None
    align: str | None = None
    alignv: str | None = None
    indent: float | None = None
    colspan: int | None = None
    rowspan: int | None = None
    rotate: float | None = None
    line: str | None = None
    line_color: str | None = None
    line_width: float | None = 0.1
    line_trim: str | None = None
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class FormatDirective:
    """A single ``.fmt()`` call: selectors plus value-formatting transforms."""

    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None
    j: int | str | Sequence[int | str] | None
    where: pl.Expr | None = None
    regex: bool = False
    digits: int | None = None
    num_fmt: str | None = "decimal"
    replace: dict | str | bool | None = None
    escape: bool | str = False
    fn: Callable | None = None
    linebreak: str | None = None
    math: bool = False
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class PlotDirective:
    """A single ``.plot()`` call."""

    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None
    j: int | str | Sequence[int | str] | None
    fun: Callable
    regex: bool = False
    data: list | None = None
    color: str = "black"
    xlim: list[float] | None = None
    height: float = 1.0
    height_px: int = 400
    width_px: int = 1200
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ImageDirective:
    """A single ``.images()`` call."""

    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None
    j: int | str | Sequence[int | str] | None
    images: list[str]
    regex: bool = False
    height: float = 1.0
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class RowGroup:
    """A row-group separator: ``label`` displayed before data row ``position``."""

    label: str
    position: int


@dataclass(frozen=True)
class ColGroup:
    """A column group: ``label`` spanning ``columns`` (0-based positions)."""

    label: str
    columns: list[int]


@dataclass(frozen=True)
class Note:
    """A footnote; ``marker`` is auto-assigned when its selectors target cells."""

    text: str
    marker: str | None = None
    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None = None
    j: int | str | Sequence[int | str] | None = None
    where: pl.Expr | None = None
    regex: bool = False
