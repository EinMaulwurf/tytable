"""
The render pipeline: resolve recorded directives into a :class:`BuiltTable`.

:func:`build` is called by :meth:`TyTable.render` and turns the lazy intent
(style / format / group / plot directives) into a backend-agnostic
:class:`BuiltTable` that the renderers consume.
"""

from __future__ import annotations

from collections.abc import Sequence
from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._directives import Note
from ._escape import escape_html, escape_typst
from ._format import apply_formats
from ._groups import merge_row_groups
from ._indices import RowLayout, resolve_i
from ._renderer import OutputFormat
from ._styling import build_meta_styles, build_style_grid
from ._utils import format_markup_num

if TYPE_CHECKING:
    from ._images import MediaContext
    from ._render_typst import TypstRenderOptions
    from ._tytable import TyTable


@dataclass
class BuiltTable:
    """Backend-specific snapshot of a fully resolved table.

    Renderers consume this object without consulting the source dataframe.
    ``data_body`` is rectangular and includes inserted row-group separator
    rows. Its ordinary strings and ``colnames_display`` have already been
    escaped for ``output``; cells produced by formatters, notes, or media may
    instead contain trusted backend markup. ``caption`` and ``notes`` remain
    raw text for the renderer to escape. ``col_groups`` also contains raw
    labels: each row is outermost-to-innermost, ``None`` is an independent
    blank cell, and ``""`` continues the preceding labelled span.

    Coordinates in ``style_grid`` and ``style_lines`` are final zero-based
    display coordinates. A grid value contains the final last-writer-wins cell
    properties. Line entries are ordered because border directives append.

    ``column_alignments`` has one
    ``"l"``/``"r"`` entry per source column. ``width`` is a table fraction,
    Typst length, or per-column sequence; ``height`` is the constructor's
    row-height value in em. ``has_background`` lets the Typst renderer avoid a
    conflicting grouped-table gutter. ``typst_options`` is an invocation-local
    copy carrying layout operations and the Typst-specific part of the resolved
    base appearance.
    """

    output: OutputFormat
    layout: RowLayout
    data_body: list[list[str]] = field(default_factory=list)
    colnames_display: list[str] = field(default_factory=list)
    column_alignments: list[str] = field(default_factory=list)
    show_colnames: bool = True
    col_groups: list[list[str | None]] = field(default_factory=list)
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
    typst_options: TypstRenderOptions | None = None


@dataclass
class _BuildState:
    """Mutable, phase-local data contract for :func:`build`.

    ``table`` is an isolated shallow working copy whose mutable directive
    lists can be reordered without changing the user's table. ``ncols`` and
    ``colnames_display`` retain source-column order. ``data_body`` is the
    mutable display matrix; ``typed_body`` is a coordinate-identical matrix of
    original Python values used by formatters and plot callbacks. Row-group
    insertion adds identical separator rows to both matrices before selectors
    resolve.

    After grouping, ``layout`` owns every source/body/display row mapping and
    ``col_groups`` is ordered outermost-to-innermost. ``escaped_cells`` and
    ``image_cells`` use final zero-based display coordinates. They identify
    trusted markup owned by formatting/media phases, so
    the later global escape pass leaves it intact while escaping every ordinary
    display string. ``media_context`` holds the invocation-local static-image
    policy and, for :meth:`TyTable.save`, its external-media destination. A
    ``None`` value uses reference-mode static images and embedded generated
    plots. The context is never stored on the source table.
    """

    table: TyTable
    output: OutputFormat
    ncols: int
    data_body: list[list[str]]
    typed_body: list[list[Any]]
    colnames_display: list[str]
    show_colnames: bool
    col_groups: list[list[str | None]] = field(default_factory=list)
    layout: RowLayout | None = None
    escaped_cells: set[tuple[int, int]] = field(default_factory=set)
    image_cells: set[tuple[int, int]] = field(default_factory=set)
    media_context: MediaContext | None = None


def _layout(state: _BuildState) -> RowLayout:
    """Return the layout after the grouping phase."""
    if state.layout is None:
        raise RuntimeError("row layout has not been resolved")
    return state.layout


def _insert_footnote_markers(
    data_body: list[list[str]],
    colnames_display: list[str],
    notes: list[Note],
    layout: RowLayout,
    output: OutputFormat,
    table: TyTable,
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

        if output == "html":
            marker_text = f"<sup>{escape_html(str(marker))}</sup>"
        elif output == "ascii":
            marker_text = f"[{marker}]"
        else:
            marker_text = f"#super[{escape_typst(marker)}]"

        j_selector = note.j
        i_vals = resolve_i(
            note.i,
            layout=layout,
            data=table._data,
        )
        layout.require_supported(
            i_vals,
            allowed={"header", "groupi", "data"},
            method="targeted notes",
        )
        j_vals = table._resolve_j(j_selector)

        for i in i_vals:
            if i == layout.header_row:
                for j in j_vals:
                    colnames_display[j] += marker_text
            else:
                ri = layout.body_index(i)
                for j in j_vals:
                    data_body[ri][j] += marker_text


def _copy_for_build(table: TyTable) -> TyTable:
    """Return a working copy whose mutable directive collections are isolated."""
    working = copy(table)
    working._style_directives = list(table._style_directives)
    working._format_directives = list(table._format_directives)
    working._plot_directives = list(table._plot_directives)
    working._image_directives = list(table._image_directives)
    working._media_directives = list(table._media_directives)
    working._row_groups = list(table._row_groups)
    working._col_group_rows = list(table._col_group_rows)
    working._notes = list(table._notes)
    working._typst_opts = copy(table._typst_opts)
    return working


def _extract_body(
    table: TyTable, output: OutputFormat, media_context: MediaContext | None = None
) -> _BuildState:
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
        colnames_display=list(table._colnames_display),
        show_colnames=table._show_colnames,
        media_context=media_context,
    )


def _column_alignments(table: TyTable) -> list[str]:
    """Return dtype-based horizontal alignment defaults for source columns."""
    return ["r" if dtype.is_numeric() else "l" for dtype in table._data.schema.values()]


def _merge_groups(state: _BuildState) -> None:
    """Insert row-group rows into both display and typed cell matrices."""
    state.data_body, row_group_positions = merge_row_groups(
        state.data_body,
        state.table._row_groups,
        state.ncols,
    )
    state.typed_body, _ = merge_row_groups(
        state.typed_body,
        state.table._row_groups,
        state.ncols,
    )
    state.col_groups = list(state.table._col_group_rows)
    state.layout = RowLayout.create(
        source_rows=state.table._data.height,
        column_group_rows=len(state.col_groups),
        has_header=state.show_colnames,
        group_body_rows=set(row_group_positions),
    )


def _apply_formatting(state: _BuildState) -> None:
    """Apply format directives and record cells containing trusted markup."""
    # Formatting owns any markup it creates (math, line breaks, or explicit
    # escaping) and reports those coordinates. The later table-wide escape
    # pass can then protect generated markup without trusting ordinary values.
    state.escaped_cells = apply_formats(
        state.data_body,
        state.typed_body,
        state.colnames_display,
        state.table,
        layout=_layout(state),
        output=state.output,
    )


def _execute_plots(state: _BuildState) -> None:
    """Replace plot targets with backend markup and track generated image cells."""
    from ._images import execute_plots

    state.image_cells = execute_plots(
        state.table,
        state.data_body,
        state.typed_body,
        state.output,
        media_context=state.media_context,
        layout=_layout(state),
    )


def _apply_global_escape(state: _BuildState) -> None:
    """Escape ordinary cells while preserving explicitly generated markup."""
    if not state.table._escape:
        return

    if state.output == "ascii":
        return
    escape = escape_html if state.output == "html" else escape_typst
    layout = _layout(state)
    for col_idx, val in enumerate(state.colnames_display):
        header_cell = (layout.header_row, col_idx)
        if layout.header_row is None or header_cell not in state.escaped_cells:
            state.colnames_display[col_idx] = escape(val)

    trusted_cells = state.escaped_cells | state.image_cells
    for row_idx, row in enumerate(state.data_body):
        display_row = layout.header_rows + row_idx
        for col_idx, val in enumerate(row):
            if (display_row, col_idx) not in trusted_cells:
                row[col_idx] = escape(val)


def _insert_footnotes(state: _BuildState) -> None:
    """Insert note markers after escaping so their markup remains intact."""
    _insert_footnote_markers(
        state.data_body,
        state.colnames_display,
        state.table._notes,
        _layout(state),
        state.output,
        state.table,
    )


def _build_style_grid(
    state: _BuildState,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    """Resolve cell and line style directives."""
    return build_style_grid(
        state.table,
        layout=_layout(state),
        output=state.output,
    )


def _apply_meta_styles(state: _BuildState) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve caption and note styles."""
    return build_meta_styles(state.table, output=state.output)


def _apply_colspans(style_grid: dict[tuple[int, int], dict[str, Any]], state: _BuildState) -> None:
    """Span each row-group label across the full table width."""
    for position in _layout(state).groupi_rows:
        style_grid.setdefault((position, 0), {})["colspan"] = state.ncols


def build(
    table: TyTable, output: OutputFormat, *, media_context: MediaContext | None = None
) -> BuiltTable:
    """
    Resolve a table's recorded directives into a backend-agnostic :class:`BuiltTable`.

    Runs the fixed pipeline: merge row groups → apply the base appearance →
    apply formats → execute plots → insert footnote markers → build the style
    grid.
    """
    if output not in ("typst", "html", "ascii"):
        raise NotImplementedError(f"output={output!r} not implemented")

    state = _extract_body(_copy_for_build(table), output, media_context)
    _merge_groups(state)
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
        layout=_layout(state),
        data_body=state.data_body,
        colnames_display=state.colnames_display,
        column_alignments=_column_alignments(state.table),
        show_colnames=state.show_colnames,
        col_groups=state.col_groups,
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
        typst_options=state.table._typst_opts,
    )
