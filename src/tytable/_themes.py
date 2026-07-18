"""Built-in base appearances resolved directly against the final row layout."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ._indices import RowLayout
    from ._tytable import TyTable

BaseTheme = Literal["default", "plain", "striped", "grid"]


def apply_base_theme(
    table: TyTable,
    layout: RowLayout,
    ncols: int,
    grid: dict[tuple[int, int], dict[str, Any]],
    lines: list[dict[str, Any]],
) -> None:
    """Seed resolved base styles before explicit user directives are applied."""
    if table._theme == "plain":
        return
    if table._theme == "striped":
        for row in layout.data_rows[::2]:
            for col in range(ncols):
                grid.setdefault((row, col), {})["background"] = "#ededed"
        return
    if table._theme == "grid":
        table._typst_opts.grid_stroke = "(paint: black)"
        for row in range(layout.total_rows):
            _add_line(lines, row, range(ncols), "tblr", 0.05)
        return

    if layout.body_rows and layout.last_row is not None:
        _add_line(lines, layout.last_row, range(ncols), "b", 0.08)
    if layout.first_row is not None:
        _add_line(lines, layout.first_row, range(ncols), "t", 0.08)
    if layout.header_row is not None:
        _add_line(lines, layout.header_row, range(ncols), "b", 0.05)


def _add_line(
    lines: list[dict[str, Any]], row: int, columns: range, sides: str, width: float
) -> None:
    for col in columns:
        lines.append(
            {
                "i": row,
                "j": col,
                "line": sides,
                "line_color": "black",
                "line_width": width,
                "line_trim": None,
            }
        )
