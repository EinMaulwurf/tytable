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
from ._renderer import OutputFormat
from ._styling import build_meta_styles, build_style_grid
from ._utils import format_markup_num

if TYPE_CHECKING:
    import polars as pl

    from ._tytable import TinyTable


@dataclass
class BuiltTable:
    """Backend-agnostic snapshot of a fully-resolved table, consumed by renderers."""

    output: OutputFormat
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


@dataclass
class _BuildState:
    """Mutable state passed between the phases of the render pipeline."""

    table: TinyTable
    output: OutputFormat
    ncols: int
    data_body: list[list[str]]
    typed_body: list[list[Any]]
    colnames_display: list[str]
    show_colnames: bool
    row_group_positions: dict[int, str] = field(default_factory=dict)
    col_groups: list[list[str | None]] = field(default_factory=list)
    nhead: int = 0
    n_merged_body: int = 0
    group_positions: set[int] = field(default_factory=set)
    escaped_cells: set[tuple[int, int]] = field(default_factory=set)
    image_cells: set[tuple[int, int]] = field(default_factory=set)


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
    output: OutputFormat,
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


def _copy_for_build(table: TinyTable) -> TinyTable:
    """Return a working copy whose mutable directive collections are isolated."""
    working = copy(table)
    working._style_directives = list(table._style_directives)
    working._deferred_style_directives = []
    working._format_directives = list(table._format_directives)
    working._plot_directives = list(table._plot_directives)
    working._image_directives = list(table._image_directives)
    working._media_directives = list(table._media_directives)
    working._row_groups = list(table._row_groups)
    working._col_group_rows = list(table._col_group_rows)
    working._notes = list(table._notes)
    return working


def _extract_body(table: TinyTable, output: OutputFormat) -> _BuildState:
    """Extract display and typed cell matrices from the source dataframe."""
    nrows = table._data.height
    ncols = table._data.width
    data_body: list[list[str]] = []
    typed_body: list[list[Any]] = []
    raw_data = table._data.to_dict(as_series=False)
    col_names = list(raw_data)

    for row_idx in range(nrows):
        display_row: list[str] = []
        typed_row: list[Any] = []
        for col_name in col_names:
            raw_val = raw_data[col_name][row_idx]
            typed_row.append(raw_val)
            display_row.append(format_markup_num(raw_val))
        data_body.append(display_row)
        typed_body.append(typed_row)

    return _BuildState(
        table=table,
        output=output,
        ncols=ncols,
        data_body=data_body,
        typed_body=typed_body,
        colnames_display=[str(colname) for colname in table._colnames],
        show_colnames=table._show_colnames,
    )


def _merge_groups(state: _BuildState) -> None:
    """Insert row-group rows into both display and typed cell matrices."""
    state.data_body, state.row_group_positions = merge_row_groups(
        state.data_body,
        state.table._row_groups,
        state.ncols,
    )
    state.typed_body, _ = merge_row_groups(
        state.typed_body,
        state.table._row_groups,
        state.ncols,
    )
    state.n_merged_body = len(state.data_body)
    state.col_groups = list(state.table._col_group_rows)
    state.nhead = (1 if state.show_colnames else 0) + len(state.col_groups)
    state.group_positions = set(state.row_group_positions)


def _run_prepare_hooks(state: _BuildState) -> None:
    """Run theme hooks after table dimensions and group positions are known."""
    state.table._nhead = state.nhead
    state.table._n_merged_body_rows = state.n_merged_body
    for hook in state.table._prepare_hooks:
        hook(state.table)


def _reorder_directives(state: _BuildState) -> None:
    """Place render-time style intent before user-recorded style directives."""
    state.table._style_directives = (
        state.table._deferred_style_directives + state.table._style_directives
    )


def _apply_formatting(state: _BuildState) -> None:
    """Apply format directives and record cells containing trusted markup."""
    state.escaped_cells = apply_formats(
        state.data_body,
        state.typed_body,
        state.colnames_display,
        state.table,
        nhead=state.nhead,
        has_header=state.show_colnames,
        n_merged_body=state.n_merged_body,
        group_positions=state.group_positions,
        output=state.output,
        colnames=state.table._colnames,
    )


def _execute_plots(state: _BuildState) -> None:
    """Replace plot targets with backend markup and track generated image cells."""
    from ._images import execute_plots

    state.image_cells = execute_plots(
        state.table,
        state.data_body,
        state.typed_body,
        state.output,
        nhead=state.nhead,
        has_header=state.show_colnames,
        n_merged_body=state.n_merged_body,
        group_positions=state.group_positions,
    )


def _apply_global_escape(state: _BuildState) -> None:
    """Escape ordinary cells while preserving explicitly generated markup."""
    if not state.table._escape:
        return

    escape = escape_html if state.output in ("html", "ascii") else escape_typst
    for col_idx, val in enumerate(state.colnames_display):
        if (-1, col_idx) not in state.escaped_cells:
            state.colnames_display[col_idx] = escape(val)

    trusted_cells = state.escaped_cells | state.image_cells
    for row_idx, row in enumerate(state.data_body):
        for col_idx, val in enumerate(row):
            if (row_idx, col_idx) not in trusted_cells:
                row[col_idx] = escape(val)


def _insert_footnotes(state: _BuildState) -> None:
    """Insert note markers after escaping so their markup remains intact."""
    _insert_footnote_markers(
        state.data_body,
        state.colnames_display,
        state.table._notes,
        state.nhead,
        state.n_merged_body,
        state.group_positions,
        state.show_colnames,
        state.table._colnames,
        state.output,
        data=state.table._data,
    )


def _build_style_grid(
    state: _BuildState,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    """Resolve cell and line style directives."""
    return build_style_grid(
        state.table,
        nhead=state.nhead,
        has_header=state.show_colnames,
        n_merged_body=state.n_merged_body,
        group_positions=state.group_positions,
        output=state.output,
    )


def _apply_meta_styles(state: _BuildState) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve caption and note styles."""
    return build_meta_styles(state.table, output=state.output)


def _apply_colspans(style_grid: dict[tuple[int, int], dict[str, Any]], state: _BuildState) -> None:
    """Span each row-group label across the full table width."""
    for position in state.row_group_positions:
        style_grid.setdefault((position, 1), {})["colspan"] = state.ncols


def build(table: TinyTable, output: OutputFormat) -> BuiltTable:
    """
    Resolve a table's recorded directives into a backend-agnostic :class:`BuiltTable`.

    Runs the fixed pipeline: merge row groups → run prepare-hooks → apply
    formats → execute plots → insert footnote markers → build the style grid.
    """
    if output not in ("typst", "html", "ascii"):
        raise NotImplementedError(f"output={output!r} not implemented")

    state = _extract_body(_copy_for_build(table), output)
    _merge_groups(state)
    _run_prepare_hooks(state)
    _reorder_directives(state)
    _apply_formatting(state)
    _execute_plots(state)
    _apply_global_escape(state)
    _insert_footnotes(state)
    style_grid, style_lines = _build_style_grid(state)
    style_caption, style_notes = _apply_meta_styles(state)
    _apply_colspans(style_grid, state)

    has_background = any("background" in props for props in style_grid.values())

    return BuiltTable(
        output=output,
        data_body=state.data_body,
        colnames_display=state.colnames_display,
        show_colnames=state.show_colnames,
        nhead=state.nhead,
        col_groups=state.col_groups,
        row_group_positions=state.row_group_positions,
        style_grid=style_grid,
        style_lines=style_lines,
        style_caption=style_caption,
        style_notes=style_notes,
        has_background=has_background,
        caption=state.table._caption,
        label=state.table._label,
        width=state.table._width,
        height=state.table._height,
        notes=state.table._notes,
    )
