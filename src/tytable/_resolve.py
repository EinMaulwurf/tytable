"""
The render pipeline: resolve recorded directives into a :class:`BuiltTable`.

:func:`build` is called by :meth:`TinyTable.render` and turns the lazy intent
(style / format / group / plot directives) into a backend-agnostic
:class:`BuiltTable` that the renderers consume.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._directives import Note
from ._escape import escape_html, escape_typst
from ._format import apply_formats
from ._groups import merge_row_groups
from ._styling import build_meta_styles, build_style_grid
from ._utils import format_markup_num

if TYPE_CHECKING:
    import polars as pl

    from ._tytable import TinyTable


@dataclass
class BuiltTable:
    """Backend-agnostic snapshot of a fully-resolved table, consumed by renderers."""

    output: str
    data_body: list[list[str]] = field(default_factory=list)
    colnames_display: list[str] = field(default_factory=list)
    show_colnames: bool = True
    nhead: int = 0
    col_groups: list[list[str | None]] = field(default_factory=list)
    row_group_positions: dict[int, str] = field(default_factory=dict)
    style_grid: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    style_lines: list[dict[str, Any]] = field(default_factory=list)
    style_caption: dict[str, Any] = field(default_factory=dict)
    style_notes: dict[str, Any] = field(default_factory=dict)
    notes: list[Note] = field(default_factory=list)
    caption: str | None = None
    label: str | None = None
    width: float | Sequence[float | str | None] | str | None = None
    height: float | None = None
    has_background: bool = False
    assets_relpath: str | None = None


def _resolve_i_internal(
    i_selector: int
    | str
    | Sequence[int | str]
    | pl.Expr
    | pl.Series
    | Callable[[dict], bool]
    | None,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
    data: pl.DataFrame | None = None,
) -> list[int] | None:
    """Thin wrapper around :func:`resolve_i` re-exported for footnote insertion."""
    from ._indices import resolve_i

    return resolve_i(
        i_selector,
        nhead=nhead,
        group_positions=group_positions,
        n_merged_body=n_merged_body,
        has_header=has_header,
        data=data,
    )


def _resolve_j_internal(
    j_selector: int | str | Sequence[int | str] | None, colnames: list[str]
) -> list[int]:
    """Thin wrapper around :func:`resolve_j` re-exported for footnote insertion."""
    from ._indices import resolve_j

    return resolve_j(j_selector, colnames)


def _insert_footnote_markers(
    data_body: list[list[str]],
    colnames_display: list[str],
    notes: list[Note],
    nhead: int,
    n_merged_body: int,
    group_positions: set[int],
    has_header: bool,
    colnames: list[str],
    output: str,
    data: pl.DataFrame | None = None,
) -> None:
    """Append superscript markers to cells targeted by a note (mutates in place)."""
    if not notes:
        return

    for note in notes:
        if note.i is None and note.j is None:
            continue
        marker = note.marker
        if marker is None:
            continue

        if output in ("html", "ascii"):
            marker_text = f"<sup>{escape_html(str(marker))}</sup>"
        else:
            marker_text = f"#super[{escape_typst(marker)}]"

        j_selector = note.j
        i_vals = _resolve_i_internal(
            note.i,
            nhead,
            has_header,
            n_merged_body,
            group_positions,
            data=data,
        )
        j_vals = _resolve_j_internal(j_selector, colnames)

        if i_vals is None:
            continue
        for i in i_vals:
            if i == 0:
                for j in j_vals:
                    ci = j - 1
                    if 0 <= ci < len(colnames_display):
                        colnames_display[ci] += marker_text
            elif i >= 1:
                ri = i - 1
                for j in j_vals:
                    ci = j - 1
                    if ri < len(data_body) and ci < len(data_body[ri]):
                        data_body[ri][ci] += marker_text


def build(table: TinyTable, output: str) -> BuiltTable:
    """
    Resolve a table's recorded directives into a backend-agnostic :class:`BuiltTable`.

    Runs the fixed pipeline: merge row groups → run prepare-hooks → apply
    formats → execute plots → insert footnote markers → build the style grid.
    """
    if output not in ("typst", "html", "ascii"):
        raise NotImplementedError(f"output={output!r} not implemented")

    # Prepare hooks record render-time intent. Replay them on a shallow working
    # copy so rendering never appends directives or resolution metadata to the
    # user's TinyTable instance.
    table = copy(table)
    table._style_directives = list(table._style_directives)
    table._format_directives = list(table._format_directives)
    table._plot_directives = list(table._plot_directives)
    table._row_groups = list(table._row_groups)
    table._col_group_rows = list(table._col_group_rows)
    table._notes = list(table._notes)

    nrows = table._data.height
    ncols = table._data.width

    data_body: list[list[str]] = []
    typed_body: list[list[Any]] = []
    raw_data = table._data.to_dict(as_series=False)
    col_names = list(raw_data.keys())

    for r in range(nrows):
        row: list[str] = []
        typed_row: list = []
        for col_idx in range(ncols):
            raw_val = raw_data[col_names[col_idx]][r]
            typed_row.append(raw_val)
            val = format_markup_num(raw_val)
            row.append(val)
        data_body.append(row)
        typed_body.append(typed_row)

    colnames_display: list[str] = []
    for c in table._colnames:
        colnames_display.append(str(c))

    show_colnames = table._show_colnames

    data_body, row_group_positions = merge_row_groups(
        data_body,
        table._row_groups,
        ncols,
    )
    typed_body, _ = merge_row_groups(
        typed_body,
        table._row_groups,
        ncols,
    )

    n_merged_body = len(data_body)
    col_groups = list(table._col_group_rows)
    nhead = (1 if show_colnames else 0) + len(col_groups)
    group_position_set = set(row_group_positions.keys())

    table._nhead = nhead
    table._n_merged_body_rows = n_merged_body

    n_style_before = len(table._style_directives)
    n_fmt_before = len(table._format_directives)

    for hook in table._prepare_hooks:
        hook(table)

    if len(table._style_directives) > n_style_before:
        added_styles = table._style_directives[n_style_before:]
        table._style_directives = added_styles + table._style_directives[:n_style_before]
    if len(table._format_directives) > n_fmt_before:
        added_formats = table._format_directives[n_fmt_before:]
        table._format_directives = added_formats + table._format_directives[:n_fmt_before]

    escaped_cells = apply_formats(
        data_body,
        typed_body,
        colnames_display,
        table,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=n_merged_body,
        group_positions=group_position_set,
        output=output,
        colnames=table._colnames,
    )

    from ._images import execute_plots

    image_cells = execute_plots(
        table,
        data_body,
        typed_body,
        output,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=n_merged_body,
        group_positions=group_position_set,
    )

    if table._escape:
        for col_idx, val in enumerate(colnames_display):
            if (-1, col_idx) not in escaped_cells:
                if output in ("html", "ascii"):
                    colnames_display[col_idx] = escape_html(val)
                else:
                    colnames_display[col_idx] = escape_typst(val)
        for r in range(len(data_body)):
            for col_idx in range(len(data_body[r])):
                if (r, col_idx) not in escaped_cells and (r, col_idx) not in image_cells:
                    val = data_body[r][col_idx]
                    if output in ("html", "ascii"):
                        data_body[r][col_idx] = escape_html(val)
                    else:
                        data_body[r][col_idx] = escape_typst(val)

    _insert_footnote_markers(
        data_body,
        colnames_display,
        table._notes,
        nhead,
        n_merged_body,
        group_position_set,
        show_colnames,
        table._colnames,
        output,
        data=table._data,
    )

    style_grid, style_lines = build_style_grid(
        table,
        nhead=nhead,
        has_header=show_colnames,
        n_merged_body=n_merged_body,
        group_positions=group_position_set,
        output=output,
    )

    style_caption, style_notes = build_meta_styles(table, output=output)

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
        style_caption=style_caption,
        style_notes=style_notes,
        has_background=has_background,
        caption=table._caption,
        label=table._label,
        width=table._width,
        height=table._height,
        notes=table._notes,
    )
