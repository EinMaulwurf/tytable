"""ASCII renderer — produces a plain-text box-drawing table for ``__repr__``."""

from __future__ import annotations

from ._renderer import Renderer
from ._resolve import BuiltTable


def _plain_text(val: str) -> str:
    """Collapse newlines in a cell value to single-line plain text."""
    return val.replace("\n", " ").replace("\r", "")


class AsciiRenderer(Renderer):
    """Render a :class:`BuiltTable` to a fixed-width ASCII table string."""

    MAX_LINE_LENGTH = 60

    def render(self, built: BuiltTable, _opts: object = None) -> str:
        """Produce the box-drawing ASCII table (header + body, columns auto-sized)."""
        max_widths = [len(str(c)) for c in built.colnames_display]

        for row in built.data_body:
            for c, val in enumerate(row):
                tv = _plain_text(str(val))
                max_widths[c] = max(max_widths[c], min(len(tv), self.MAX_LINE_LENGTH))

        def sep() -> str:
            return "+" + "+".join("-" * (w + 2) for w in max_widths) + "+"

        def format_cell(val: str, width: int) -> str:
            tv = _plain_text(str(val))
            if len(tv) > width:
                tv = tv[: width - 1] + "…"
            return tv.ljust(width)

        lines: list[str] = []
        lines.append(sep())

        if built.show_colnames:
            header = (
                "| "
                + " | ".join(
                    format_cell(c, max_widths[i]) for i, c in enumerate(built.colnames_display)
                )
                + " |"
            )
            lines.append(header)
            lines.append(sep())

        for row in built.data_body:
            line = (
                "| "
                + " | ".join(format_cell(val, max_widths[i]) for i, val in enumerate(row))
                + " |"
            )
            lines.append(line)

        lines.append(sep())
        return "\n".join(lines)
