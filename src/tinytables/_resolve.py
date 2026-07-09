from __future__ import annotations

from dataclasses import dataclass, field

from ._escape import escape_typst
from ._styling import build_style_grid
from ._utils import format_markup_num


@dataclass
class BuiltTable:
    output: str
    data_body: list[list[str]] = field(default_factory=list)
    colnames_display: list[str] = field(default_factory=list)
    show_colnames: bool = True
    nhead: int = 0
    col_groups: list = field(default_factory=list)
    row_group_positions: dict = field(default_factory=dict)
    style_grid: dict = field(default_factory=dict)
    style_lines: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    caption: str | None = None
    width: float | list[float] | None = None
    height: float | None = None
    has_background: bool = False
    assets_relpath: str | None = None


def build(table, output: str) -> BuiltTable:
    if output not in ("typst",):
        raise NotImplementedError(f"output={output!r} not implemented in Phase 1")

    nrows = table._data.height
    ncols = table._data.width

    data_body: list[list[str]] = []
    raw_data = table._data.to_dict(as_series=False)
    col_names = list(raw_data.keys())

    for r in range(nrows):
        row: list[str] = []
        for c in range(ncols):
            raw_val = raw_data[col_names[c]][r]
            val = format_markup_num(raw_val)
            if table._escape:
                val = escape_typst(val)
            row.append(val)
        data_body.append(row)

    colnames_display: list[str] = []
    for c in table._colnames:
        name = str(c)
        if table._escape:
            name = escape_typst(name)
        colnames_display.append(name)

    show_colnames = table._show_colnames
    nhead = (1 if show_colnames else 0) + len(table._col_groups)

    style_grid, style_lines = build_style_grid(
        table,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=nrows,
        group_positions=set(),
        output=output,
    )
    has_background = any("background" in props for props in style_grid.values())

    return BuiltTable(
        output=output,
        data_body=data_body,
        colnames_display=colnames_display,
        show_colnames=show_colnames,
        nhead=nhead,
        style_grid=style_grid,
        style_lines=style_lines,
        has_background=has_background,
        caption=table._caption,
        width=table._width,
        height=table._height,
    )
