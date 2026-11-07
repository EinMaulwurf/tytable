"""
Apply column-wise formatting callbacks and preserve semantic output.

Applied during the render pipeline by :func:`tytable._resolve.build`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from tytable._formatted import _DisplayText, _FormattedText, _source
from tytable._indices import resolve_i, resolve_where

if TYPE_CHECKING:
    from tytable._directives import FormatDirective
    from tytable._indices import RowLayout
    from tytable._tytable import TyTable

Cell = tuple[int, int]


def _resolve_target_cells(
    i_vals: list[int],
    j_vals: list[int],
    layout: RowLayout,
) -> list[Cell]:
    """Return final display coordinates supported by value formatting."""
    layout.require_supported(i_vals, allowed={"header", "groupi", "data"}, method=".fmt()")
    return [(row, col) for row in i_vals for col in j_vals]


def _typed_value(
    cell: Cell, typed_body: list[list[Any]], colnames: list[str], layout: RowLayout
) -> object | None:
    """Return the original typed value for a body or header cell."""
    display_row, col_idx = cell
    if display_row == layout.header_row:
        return colnames[col_idx]
    row_idx = layout.body_index(display_row)
    if row_idx < len(typed_body) and col_idx < len(typed_body[row_idx]):
        return typed_body[row_idx][col_idx]
    return None


def _cell_value(
    cell: Cell,
    data_body: list[list[str]],
    colnames_display: list[str],
    layout: RowLayout,
) -> str:
    """Read the current rendered value of a body or header cell."""
    display_row, col_idx = cell
    if display_row == layout.header_row:
        return colnames_display[col_idx]
    return data_body[layout.body_index(display_row)][col_idx]


def _set_cell_value(
    cell: Cell,
    value: object,
    data_body: list[list[str]],
    colnames_display: list[str],
    layout: RowLayout,
) -> None:
    """Set the rendered value of a body or header cell."""
    display_row, col_idx = cell
    if display_row == layout.header_row:
        colnames_display[col_idx] = value if isinstance(value, str) else str(value)
    else:
        data_body[layout.body_index(display_row)][col_idx] = (
            value if isinstance(value, str) else str(value)
        )


def _apply_fn(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
    layout: RowLayout,
    output: str,
    escape: bool,
) -> dict[Cell, str]:
    """Apply a column-wise transform to the selected cells."""
    generated_markup: dict[Cell, str] = {}
    if directive.fn is None:
        return generated_markup
    col_to_rows: dict[int, list[int]] = {}
    for row_idx, col_idx in cells:
        col_to_rows.setdefault(col_idx, []).append(row_idx)
    for col_idx, rows in col_to_rows.items():
        column_cells = [(row_idx, col_idx) for row_idx in sorted(rows)]
        if directive.fn_values == "typed":
            values = [_typed_value(cell, typed_body, colnames, layout) for cell in column_cells]
        else:
            values = [
                _cell_value(cell, data_body, colnames_display, layout) for cell in column_cells
            ]
        result = directive.fn(values)
        if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
            raise TypeError(f"fn() must return a non-string sequence, got {type(result).__name__}")
        if len(result) != len(values):
            raise ValueError(f"fn() returned {len(result)} items, expected {len(values)}")
        for cell, value in zip(column_cells, result, strict=True):
            source = _source(value)
            if isinstance(source, _FormattedText):
                value = _DisplayText(source.render(output, escape=escape), source)
                generated_markup[cell] = value
            _set_cell_value(cell, value, data_body, colnames_display, layout)

    return generated_markup


def apply_formats(
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    table: TyTable,
    *,
    layout: RowLayout,
    output: str,
) -> set[tuple[int, int]]:
    """Apply every format directive and return trusted display coordinates."""
    escaped_cells: set[tuple[int, int]] = set()

    for d in table._format_directives:
        if d.output is not None and output not in d.output:
            continue

        i_vals = resolve_i(
            d.i,
            layout=layout,
            data=table._data,
        )
        j_vals = table._resolve_j(d.j)

        target_cells = _resolve_target_cells(i_vals, j_vals, layout)
        if d.where is not None:
            where_cells = resolve_where(
                d.where,
                data=table._data,
                layout=layout,
            )
            target_cells = [cell for cell in target_cells if cell in where_cells]
        values_before = {
            cell: _cell_value(cell, data_body, colnames_display, layout) for cell in target_cells
        }
        generated_markup = _apply_fn(
            target_cells,
            d,
            data_body,
            typed_body,
            colnames_display,
            table._source_colnames,
            layout,
            output,
            table._escape,
        )
        escaped_cells.difference_update(
            cell
            for cell, before in values_before.items()
            if _cell_value(cell, data_body, colnames_display, layout) != before
        )
        escaped_cells.update(generated_markup)

    return escaped_cells
