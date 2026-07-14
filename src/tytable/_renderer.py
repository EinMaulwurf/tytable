"""Shared renderer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._resolve import BuiltTable


class Renderer(ABC):
    """Convert a resolved table into one output format."""

    @abstractmethod
    def render(self, built: BuiltTable) -> str:
        """Render ``built`` to a string."""
