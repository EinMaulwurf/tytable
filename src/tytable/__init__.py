"""Public exports for :mod:`tytable`.

Besides the :func:`tt` factory and :class:`TyTable`, the package exposes
:data:`THEMES` for theme discovery and advanced composition. Apply built-ins
through the chainable ``TyTable.theme_*()`` methods.
"""

from ._themes import THEMES
from ._types import NoteDict
from ._tytable import TyTable, tt

#: Built-in theme registry mapping names to ``theme(table)`` callables.
#: Normal application code should use the typed ``TyTable.theme_*()`` methods.

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("tytable")
    except PackageNotFoundError:
        __version__ = "0.0.0"

__all__ = ["tt", "TyTable", "THEMES", "NoteDict"]
