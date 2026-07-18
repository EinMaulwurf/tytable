"""ASCII renderer — produces a plain-text box-drawing table for ``__repr__``."""

from __future__ import annotations

from wcwidth import wcswidth, wcwidth

from ._renderer import Renderer
from ._resolve import BuiltTable


def _plain_text(val: str) -> str:
    """Collapse newlines in a cell value to single-line plain text."""
    return val.replace("\n", " ").replace("\r", "")


def _display_width(val: str) -> int:
    """Return the number of terminal columns occupied by ``val``."""
    width = wcswidth(val)
    return width if width >= 0 else sum(max(wcwidth(char), 0) for char in val)


def _truncate(val: str, width: int) -> str:
    """Truncate ``val`` to a terminal display width, reserving room for an ellipsis."""
    if _display_width(val) <= width:
        return val

    target = max(width - 1, 0)
    used = 0
    chars: list[str] = []
    for char in val:
        char_width = max(wcwidth(char), 0)
        if used + char_width > target:
            break
        chars.append(char)
        used += char_width
    return "".join(chars) + ("…" if width > 0 else "")


def _pad(val: str, width: int, align: str) -> str:
    """Pad ``val`` to ``width`` terminal columns using the requested alignment."""
    padding = max(width - _display_width(val), 0)
    if align in ("r", "right"):
        return " " * padding + val
    if align in ("c", "center"):
        left = padding // 2
        return " " * left + val + " " * (padding - left)
    return val + " " * padding


class AsciiRenderer(Renderer):
    """Render a :class:`BuiltTable` to a fixed-width ASCII table string."""

    MAX_CELL_WIDTH = 60

    def render(self, built: BuiltTable) -> str:
        """Produce the box-drawing ASCII table (header + body, columns auto-sized)."""
        headers = [_plain_text(str(c)) for c in built.colnames_display]
        body = [[_plain_text(str(val)) for val in row] for row in built.data_body]
        max_widths = [min(_display_width(c), self.MAX_CELL_WIDTH) for c in headers]

        for row in body:
            for c, val in enumerate(row):
                max_widths[c] = max(max_widths[c], min(_display_width(val), self.MAX_CELL_WIDTH))

        def sep() -> str:
            return "+" + "+".join("-" * (w + 2) for w in max_widths) + "+"

        def format_cell(val: str, width: int, align: str) -> str:
            return _pad(_truncate(val, width), width, align)

        lines: list[str] = []
        if built.caption is not None:
            lines.extend((_plain_text(built.caption), ""))
        lines.append(sep())

        if built.show_colnames:
            header_row = built.layout.header_row
            if header_row is None:
                raise RuntimeError("visible column names require a header row")
            header = (
                "| "
                + " | ".join(
                    format_cell(
                        c,
                        max_widths[i],
                        built.style_grid.get((header_row, i), {}).get(
                            "align", built.column_alignments[i]
                        ),
                    )
                    for i, c in enumerate(headers)
                )
                + " |"
            )
            lines.append(header)
            lines.append(sep())

        for body_idx, row in enumerate(body):
            display_row = built.layout.header_rows + body_idx
            line = (
                "| "
                + " | ".join(
                    format_cell(
                        val,
                        max_widths[i],
                        built.style_grid.get((display_row, i), {}).get(
                            "align",
                            "l"
                            if display_row in built.layout.groupi_rows
                            else built.column_alignments[i],
                        ),
                    )
                    for i, val in enumerate(row)
                )
                + " |"
            )
            lines.append(line)

        lines.append(sep())
        if built.notes:
            lines.append("")
            for note in built.notes:
                marker = f"[{note.marker}] " if note.marker is not None else ""
                lines.append(marker + _plain_text(note.text))
        return "\n".join(lines)
