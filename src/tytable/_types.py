"""Public typing helpers for :mod:`tytable`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict


class NoteDict(TypedDict, total=False):
    """Dictionary form of a table note accepted by :func:`tytable.tt`.

    ``text`` is the footer text and ``marker`` is an optional explicit marker.
    ``i`` and ``j`` use the normal row and column selector forms; when either
    target is present and ``marker`` is omitted, tytable assigns a number.
    """

    text: str
    marker: str | None
    i: int | str | Sequence[int | str] | None
    j: int | str | Sequence[int | str] | None
