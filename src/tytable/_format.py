"""
Value formatting: numeric, replace, escape, function, line-break, and math transforms.

Applied during the render pipeline by :func:`tytable._resolve.build`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ._escape import escape_typst
from ._indices import resolve_i, resolve_where

if TYPE_CHECKING:
    from ._directives import FormatDirective
    from ._indices import RowLayout
    from ._tytable import TyTable

Cell = tuple[int, int]


def _is_numeric_typed(val: object) -> bool:
    """True for ints/floats but not bools (which are technically int subclasses)."""
    if isinstance(val, bool):
        return False
    return isinstance(val, (int, float))


def _fmt_numeric_decimal(val: Any, digits: int) -> str:
    """Format a number with a fixed number of decimal places."""
    return f"{float(val):.{digits}f}"


def _fmt_numeric_significant(val: Any, digits: int) -> str:
    """Format a number to a given number of significant figures."""
    return f"{float(val):.{digits}g}"


def _fmt_numeric_scientific(val: Any, digits: int, output: str) -> str:
    """Format a number using backend-native scientific notation."""
    formatted = f"{float(val):.{digits}e}"
    if "e" not in formatted:
        return formatted

    mantissa, raw_exponent = formatted.split("e", maxsplit=1)
    exponent = int(raw_exponent)
    if output == "typst":
        exponent_expr = f"({exponent})" if exponent < 0 else str(exponent)
        return f"${mantissa} times 10^{exponent_expr}$"
    if output == "html":
        return f"{mantissa} &times; 10<sup>{exponent}</sup>"
    return f"{mantissa} * 10^{exponent}"


def _matches(o: object, typed: object, s: str) -> bool:
    """Check whether a ``replace`` key matches a typed value or its string form (handles null/nan/inf)."""
    if o is None:
        return typed is None
    if isinstance(o, float) and math.isnan(o):
        return isinstance(typed, float) and math.isnan(typed)
    if isinstance(o, float) and math.isinf(o):
        return isinstance(typed, float) and math.isinf(typed) and (typed > 0) == (o > 0)
    if isinstance(o, str):
        lo = o.lower()
        if lo == "null":
            return typed is None
        if lo == "nan":
            return isinstance(typed, float) and math.isnan(typed)
        if lo == "inf":
            return isinstance(typed, float) and math.isinf(typed) and typed > 0
        if lo == "-inf":
            return isinstance(typed, float) and math.isinf(typed) and typed < 0
    return typed == o or s == str(o)


def _apply_replace(typed_val: object, current_str: str, replace: object) -> str:
    """Apply a ``replace`` spec (``True``, a fill string, or an ``{old: new}`` dict) to one cell."""
    if replace is True:
        if typed_val is None or (isinstance(typed_val, float) and math.isnan(typed_val)):
            return " "
        return current_str
    if isinstance(replace, str):
        if typed_val is None or (isinstance(typed_val, float) and math.isnan(typed_val)):
            return replace
        return current_str
    if isinstance(replace, dict):
        mapping: dict = {}
        for k, v in replace.items():
            if isinstance(k, list):
                for item in k:
                    mapping[item] = v
            else:
                mapping[k] = v
        for old, new in mapping.items():
            if _matches(old, typed_val, current_str):
                return str(new)
    return current_str


def _apply_escape(current_str: str, escape_spec: object, output: str) -> str:
    """Re-escape a cell string for the target backend when ``fmt(escape=...)`` is set."""
    if escape_spec is True or escape_spec == "typst":
        if output == "html":
            from ._escape import escape_html

            return escape_html(current_str)
        if output == "ascii":
            return current_str
        return escape_typst(current_str)
    return current_str


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
        colnames_display[col_idx] = str(value)
    else:
        data_body[layout.body_index(display_row)][col_idx] = str(value)


def _apply_digits(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
    output: str,
    layout: RowLayout,
) -> dict[Cell, str]:
    """Apply numeric formatting and return any generated backend markup."""
    if directive.digits is None:
        return {}
    formatters = {
        "decimal": _fmt_numeric_decimal,
        "significant": _fmt_numeric_significant,
    }
    formatter = formatters.get(directive.num_fmt or "decimal", _fmt_numeric_decimal)
    generated_markup: dict[Cell, str] = {}
    for cell in cells:
        typed_val = _typed_value(cell, typed_body, colnames, layout)
        if _is_numeric_typed(typed_val):
            if directive.num_fmt == "scientific":
                formatted = _fmt_numeric_scientific(typed_val, directive.digits, output)
                generated_markup[cell] = formatted
            else:
                formatted = formatter(typed_val, directive.digits)
            _set_cell_value(cell, formatted, data_body, colnames_display, layout)
    return generated_markup


def _apply_fn(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    layout: RowLayout,
) -> None:
    """Apply a column-wise transform to the selected cells."""
    if directive.fn is None:
        return
    col_to_rows: dict[int, list[int]] = {}
    for row_idx, col_idx in cells:
        col_to_rows.setdefault(col_idx, []).append(row_idx)
    for col_idx, rows in col_to_rows.items():
        column_cells = [(row_idx, col_idx) for row_idx in sorted(rows)]
        values = [_cell_value(cell, data_body, colnames_display, layout) for cell in column_cells]
        result = directive.fn(values)
        if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
            raise TypeError(f"fn() must return a non-string sequence, got {type(result).__name__}")
        if len(result) != len(values):
            raise ValueError(f"fn() returned {len(result)} items, expected {len(values)}")
        for cell, value in zip(column_cells, result, strict=True):
            _set_cell_value(cell, value, data_body, colnames_display, layout)


def _apply_replacements(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
    layout: RowLayout,
) -> None:
    """Apply replacement rules to the selected cells."""
    if directive.replace is None:
        return
    for cell in cells:
        formatted = _apply_replace(
            _typed_value(cell, typed_body, colnames, layout),
            _cell_value(cell, data_body, colnames_display, layout),
            directive.replace,
        )
        _set_cell_value(cell, formatted, data_body, colnames_display, layout)


def _apply_escapes(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    output: str,
    layout: RowLayout,
) -> set[Cell]:
    """Apply directive-level escaping and return the escaped cell coordinates."""
    if not directive.escape:
        return set()
    for cell in cells:
        formatted = _apply_escape(
            _cell_value(cell, data_body, colnames_display, layout), directive.escape, output
        )
        _set_cell_value(cell, formatted, data_body, colnames_display, layout)
    return set(cells)


def _apply_linebreaks(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    output: str,
    *,
    global_escape: bool,
    escaped_cells: set[Cell],
    layout: RowLayout,
) -> dict[Cell, str]:
    """Replace a literal marker with safe backend-native line-break markup."""
    marker = directive.linebreak
    separators = {"typst": " \\ ", "html": "<br>"}
    separator = separators.get(output)
    if marker is None or separator is None:
        return {}

    generated_markup: dict[Cell, str] = {}
    for cell in cells:
        current = _cell_value(cell, data_body, colnames_display, layout)
        if marker not in current:
            continue
        chunks = current.split(marker)
        math_content = directive.math and output == "typst"
        if (
            not math_content
            and cell not in escaped_cells
            and (global_escape or bool(directive.escape))
        ):
            chunks = [_apply_escape(chunk, True, output) for chunk in chunks]
        formatted = separator.join(chunks)
        _set_cell_value(cell, formatted, data_body, colnames_display, layout)
        generated_markup[cell] = formatted
    return generated_markup


def _apply_math(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    output: str,
    layout: RowLayout,
) -> dict[Cell, str]:
    """Wrap selected values in Typst math, leaving other backends unchanged."""
    if not directive.math or output != "typst":
        return {}

    generated_markup: dict[Cell, str] = {}
    for cell in cells:
        current = _cell_value(cell, data_body, colnames_display, layout)
        formatted = current if current.startswith("$") and current.endswith("$") else f"${current}$"
        _set_cell_value(cell, formatted, data_body, colnames_display, layout)
        generated_markup[cell] = formatted
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
        j_vals = table._resolve_j(d.j, regex=d.regex)

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
        generated_markup = _apply_digits(
            target_cells,
            d,
            data_body,
            typed_body,
            colnames_display,
            table._source_colnames,
            output,
            layout,
        )
        _apply_fn(target_cells, d, data_body, colnames_display, layout)
        _apply_replacements(
            target_cells,
            d,
            data_body,
            typed_body,
            colnames_display,
            table._source_colnames,
            layout,
        )
        generated_markup.update(
            _apply_linebreaks(
                target_cells,
                d,
                data_body,
                colnames_display,
                output,
                global_escape=table._escape,
                escaped_cells=escaped_cells,
                layout=layout,
            )
        )
        generated_markup.update(
            _apply_math(target_cells, d, data_body, colnames_display, output, layout)
        )
        intact_markup = {
            cell
            for cell, generated in generated_markup.items()
            if _cell_value(cell, data_body, colnames_display, layout) == generated
        }
        escape_targets = [
            cell for cell in target_cells if cell not in intact_markup and cell not in escaped_cells
        ]
        explicitly_escaped = _apply_escapes(
            escape_targets, d, data_body, colnames_display, output, layout
        )
        changed_cells = {
            cell
            for cell, before in values_before.items()
            if _cell_value(cell, data_body, colnames_display, layout) != before
        }
        escaped_cells.difference_update(changed_cells)
        escaped_cells.update(intact_markup | explicitly_escaped)

    return escaped_cells
