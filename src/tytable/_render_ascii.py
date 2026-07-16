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

    def render(self, built: BuiltTable) -> str:
        """Produce the box-drawing ASCII table (header + body, columns auto-sized)."""
        max_widths = [len(str(c)) for c in built.colnames_display]

        for row in built.data_body:
            for c, val in enumerate(row):
                tv = _plain_text(str(val))
                max_widths[c] = max(max_widths[c], min(len(tv), self.MAX_LINE_LENGTH))

        def sep() -> str:
            return "+" + "+".join("-" * (w + 2) for w in max_widths) + "+"

        def format_cell(val: str, width: int, align: str) -> str:
            tv = _plain_text(str(val))
            if len(tv) > width:
                tv = tv[: width - 1] + "…"
            if align in ("r", "right"):
                return tv.rjust(width)
            if align in ("c", "center"):
                return tv.center(width)
            return tv.ljust(width)

        lines: list[str] = []
        lines.append(sep())

        if built.show_colnames:
            header = (
                "| "
                + " | ".join(
                    format_cell(
                        c,
                        max_widths[i],
                        built.style_grid.get((0, i + 1), {}).get(
                            "align", built.column_alignments[i]
                        ),
                    )
                    for i, c in enumerate(built.colnames_display)
                )
                + " |"
            )
            lines.append(header)
            lines.append(sep())

        for row_idx, row in enumerate(built.data_body, start=1):
            line = (
                "| "
                + " | ".join(
                    format_cell(
                        val,
                        max_widths[i],
                        built.style_grid.get((row_idx, i + 1), {}).get(
                            "align",
                            "l"
                            if row_idx in built.row_group_positions
                            else built.column_alignments[i],
                        ),
                    )
                    for i, val in enumerate(row)
                )
                + " |"
            )
            lines.append(line)

        lines.append(sep())
        return "\n".join(lines)
