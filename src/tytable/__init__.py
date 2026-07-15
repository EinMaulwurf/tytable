"""Public exports for :mod:`tytable`.

Besides the :func:`tt` factory and :class:`TyTable`, the package exposes
:data:`THEMES`, the registry of built-in theme callables.
"""

from ._themes import THEMES
from ._tytable import TyTable, tt

#: Built-in theme registry mapping public names to ``theme(table)`` callables.
#: Pass a key to ``tt(theme=...)`` / ``TyTable.theme()``, or inspect and call
#: a registry value when building a custom theme.

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("tytable")
    except PackageNotFoundError:
        __version__ = "0.0.0"

__all__ = ["tt", "TyTable", "THEMES"]
