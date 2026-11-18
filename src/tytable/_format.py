"""
Apply column-wise formatting callbacks and preserve semantic output.

Applied during the render pipeline by :func:`tytable._resolve.build`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from tytable._formatted import _FormattedText
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
    """Read the current display value of a body or header cell."""
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
    """Set the display value of a body or header cell."""
    display_row, col_idx = cell
    text = value if isinstance(value, str) else str(value)
    if display_row == layout.header_row:
        colnames_display[col_idx] = text
    else:
        data_body[layout.body_index(display_row)][col_idx] = text


def _apply_fn(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
    layout: RowLayout,
    output: str,
    directive_number: int,
    semantic_cells: set[Cell],
) -> None:
    """Apply a column-wise transform to the selected cells."""
    fn = directive.fn
    if fn is None:
        return
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
        try:
            result = fn(values)
            if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
                raise TypeError(
                    f"fn() must return a non-string sequence, got {type(result).__name__}"
                )
            if len(result) != len(values):
                raise ValueError(f"fn() returned {len(result)} items, expected {len(values)}")
            for cell, value in zip(column_cells, result, strict=True):
                _set_cell_value(cell, value, data_body, colnames_display, layout)
                if isinstance(value, _FormattedText):
                    semantic_cells.add(cell)
                else:
                    semantic_cells.discard(cell)
        except Exception as exc:
            error_type = (
                TypeError
                if isinstance(exc, TypeError)
                else ValueError
                if isinstance(exc, ValueError)
                else RuntimeError
            )
            raise error_type(
                f".fmt() directive {directive_number}, column {colnames[col_idx]!r}, "
                f"output {output!r}: {exc}"
            ) from exc


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
    semantic_cells: set[Cell] = set()

    for directive_number, d in enumerate(table._format_directives, start=1):
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
        _apply_fn(
            target_cells,
            d,
            data_body,
            typed_body,
            colnames_display,
            table._source_colnames,
            layout,
            output,
            directive_number,
            semantic_cells,
        )

    for cell in semantic_cells:
        value = _cell_value(cell, data_body, colnames_display, layout)
        assert isinstance(value, _FormattedText)
        rendered = value.render(output, escape=table._escape)
        _set_cell_value(cell, rendered, data_body, colnames_display, layout)

    return semantic_cells
