from __future__ import annotations

from dataclasses import dataclass, field

from ._escape import escape_typst
from ._format import apply_formats
from ._groups import merge_row_groups
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
    typed_body: list[list] = []
    raw_data = table._data.to_dict(as_series=False)
    col_names = list(raw_data.keys())

    for r in range(nrows):
        row: list[str] = []
        typed_row: list = []
        for c in range(ncols):
            raw_val = raw_data[col_names[c]][r]
            typed_row.append(raw_val)
            val = format_markup_num(raw_val)
            row.append(val)
        data_body.append(row)
        typed_body.append(typed_row)

    colnames_display: list[str] = []
    for c in table._colnames:
        name = str(c)
        if table._escape:
            name = escape_typst(name)
        colnames_display.append(name)

    show_colnames = table._show_colnames

    data_body, row_group_positions = merge_row_groups(
        data_body, table._row_groups, ncols,
    )
    typed_body, _ = merge_row_groups(
        typed_body, table._row_groups, ncols,
    )

    n_merged_body = len(data_body)
    col_groups = list(table._col_group_rows)
    nhead = (1 if show_colnames else 0) + len(col_groups)

    group_position_set = set(row_group_positions.keys())

    escaped_cells = apply_formats(
        data_body, typed_body, table,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=n_merged_body,
        group_positions=group_position_set,
        output=output,
        colnames=table._colnames,
    )

    if table._escape:
        for r in range(len(data_body)):
            for c in range(len(data_body[r])):
                if (r, c) not in escaped_cells:
                    data_body[r][c] = escape_typst(data_body[r][c])

    style_grid, style_lines = build_style_grid(
        table,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=n_merged_body,
        group_positions=group_position_set,
        output=output,
    )

    for pos, _label in row_group_positions.items():
        cell = style_grid.setdefault((pos, 1), {})
        cell["colspan"] = ncols

    has_background = any("background" in props for props in style_grid.values())

    return BuiltTable(
        output=output,
        data_body=data_body,
        colnames_display=colnames_display,
        show_colnames=show_colnames,
        nhead=nhead,
        col_groups=col_groups,
        row_group_positions=row_group_positions,
        style_grid=style_grid,
        style_lines=style_lines,
        has_background=has_background,
        caption=table._caption,
        width=table._width,
        height=table._height,
    )
