"""Public typing helpers for :mod:`tytable`."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import polars as pl


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
    j: int | str | Sequence[int | str] | None
    where: pl.Expr | None
    regex: bool
