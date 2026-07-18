"""Public exports for :mod:`tytable`.

The public API consists of the :func:`tt` factory, :class:`TyTable`, and note
typing helpers.
"""

from ._types import NoteDict
from ._tytable import TyTable, tt

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("tytable")
    except PackageNotFoundError:
        __version__ = "0.0.0"

__all__ = ["tt", "TyTable", "NoteDict"]
