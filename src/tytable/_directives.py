from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class StyleDirective:
    i: int | str | list[int] | None
    j: int | str | list[int] | None
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
    line: str | None = None
    line_color: str | None = None
    line_width: float | None = 0.1
    line_trim: str | None = None
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class FormatDirective:
    i: int | str | list[int] | None
    j: int | str | list[int] | None
    digits: int | None = None
    num_fmt: str | None = "decimal"
    replace: dict | None = None
    escape: bool | str = False
    fn: Callable | None = None
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class PlotDirective:
    i: int | str | list[int] | None
    j: int | str | list[int] | None
    fun: Callable | None = None
    data: list | None = None
    images: list[str] | None = None
    color: str = "black"
    xlim: list[float] | None = None
    height: float = 1.0
    height_px: int = 400
    width_px: int = 1200
    output: tuple[str, ...] | None = None


@dataclass(frozen=True)
class RowGroup:
    label: str
    position: int


@dataclass(frozen=True)
class ColGroup:
    label: str
    columns: list[int]


@dataclass(frozen=True)
class Note:
    text: str
    marker: str | None = None
    i: list[int] | None = None
    j: list[int] | None = None
