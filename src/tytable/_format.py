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
    data_body: list[list[str]],
    colnames_display: list[str],
) -> list[Cell]:
    """Translate resolved table coordinates into body/header cell coordinates."""
    target_cells: list[Cell] = []
    for i_idx in i_vals:
        if i_idx == 0:
            target_cells.extend(
                (-1, j_idx - 1) for j_idx in j_vals if 0 < j_idx <= len(colnames_display)
            )
            continue
        row_idx = i_idx - 1
        if row_idx < 0 or row_idx >= len(data_body):
            continue
        target_cells.extend(
            (row_idx, j_idx - 1) for j_idx in j_vals if 0 < j_idx <= len(data_body[row_idx])
        )
    return target_cells


def _typed_value(cell: Cell, typed_body: list[list[Any]], colnames: list[str]) -> object | None:
    """Return the original typed value for a body or header cell."""
    row_idx, col_idx = cell
    if row_idx == -1:
        return colnames[col_idx]
    if row_idx < len(typed_body) and col_idx < len(typed_body[row_idx]):
        return typed_body[row_idx][col_idx]
    return None


def _cell_value(cell: Cell, data_body: list[list[str]], colnames_display: list[str]) -> str:
    """Read the current rendered value of a body or header cell."""
    row_idx, col_idx = cell
    return colnames_display[col_idx] if row_idx == -1 else data_body[row_idx][col_idx]


def _set_cell_value(
    cell: Cell,
    value: object,
    data_body: list[list[str]],
    colnames_display: list[str],
) -> None:
    """Set the rendered value of a body or header cell."""
    row_idx, col_idx = cell
    if row_idx == -1:
        colnames_display[col_idx] = str(value)
    else:
        data_body[row_idx][col_idx] = str(value)


def _apply_digits(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
    output: str,
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
        typed_val = _typed_value(cell, typed_body, colnames)
        if _is_numeric_typed(typed_val):
            if directive.num_fmt == "scientific":
                formatted = _fmt_numeric_scientific(typed_val, directive.digits, output)
                generated_markup[cell] = formatted
            else:
                formatted = formatter(typed_val, directive.digits)
            _set_cell_value(cell, formatted, data_body, colnames_display)
    return generated_markup


def _apply_fn(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
) -> None:
    """Apply a column-wise transform to the selected cells."""
    if directive.fn is None:
        return
    col_to_rows: dict[int, list[int]] = {}
    for row_idx, col_idx in cells:
        col_to_rows.setdefault(col_idx, []).append(row_idx)
    for col_idx, rows in col_to_rows.items():
        column_cells = [(row_idx, col_idx) for row_idx in sorted(rows)]
        values = [_cell_value(cell, data_body, colnames_display) for cell in column_cells]
        result = directive.fn(values)
        if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
            raise TypeError(f"fn() must return a non-string sequence, got {type(result).__name__}")
        if len(result) != len(values):
            raise ValueError(f"fn() returned {len(result)} items, expected {len(values)}")
        for cell, value in zip(column_cells, result, strict=True):
            _set_cell_value(cell, value, data_body, colnames_display)


def _apply_replacements(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    colnames: list[str],
) -> None:
    """Apply replacement rules to the selected cells."""
    if directive.replace is None:
        return
    for cell in cells:
        formatted = _apply_replace(
            _typed_value(cell, typed_body, colnames),
            _cell_value(cell, data_body, colnames_display),
            directive.replace,
        )
        _set_cell_value(cell, formatted, data_body, colnames_display)


def _apply_escapes(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    output: str,
) -> set[Cell]:
    """Apply directive-level escaping and return the escaped cell coordinates."""
    if not directive.escape:
        return set()
    for cell in cells:
        formatted = _apply_escape(
            _cell_value(cell, data_body, colnames_display), directive.escape, output
        )
        _set_cell_value(cell, formatted, data_body, colnames_display)
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
) -> dict[Cell, str]:
    """Replace a literal marker with safe backend-native line-break markup."""
    marker = directive.linebreak
    separators = {"typst": " \\ ", "html": "<br>"}
    separator = separators.get(output)
    if marker is None or separator is None:
        return {}

    generated_markup: dict[Cell, str] = {}
    for cell in cells:
        current = _cell_value(cell, data_body, colnames_display)
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
        _set_cell_value(cell, formatted, data_body, colnames_display)
        generated_markup[cell] = formatted
    return generated_markup


def _apply_math(
    cells: list[Cell],
    directive: FormatDirective,
    data_body: list[list[str]],
    colnames_display: list[str],
    output: str,
) -> dict[Cell, str]:
    """Wrap selected values in Typst math, leaving other backends unchanged."""
    if not directive.math or output != "typst":
        return {}

    generated_markup: dict[Cell, str] = {}
    for cell in cells:
        current = _cell_value(cell, data_body, colnames_display)
        formatted = current if current.startswith("$") and current.endswith("$") else f"${current}$"
        _set_cell_value(cell, formatted, data_body, colnames_display)
        generated_markup[cell] = formatted
    return generated_markup


def apply_formats(
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    colnames_display: list[str],
    table: TyTable,
    *,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
    output: str,
) -> set[tuple[int, int]]:
    """Apply every ``FormatDirective``, returning cells that were explicitly escaped.

    Body cells use their zero-based row index.  Header cells use row ``-1`` so
    callers can distinguish them when applying the table-wide escape pass.
    """
    escaped_cells: set[tuple[int, int]] = set()

    for d in table._format_directives:
        if d.output is not None and output not in d.output:
            continue

        i_vals = resolve_i(
            d.i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
            data=table._data,
        )
        j_vals = table._resolve_j(d.j, regex=d.regex)

        target_cells = _resolve_target_cells(i_vals, j_vals, data_body, colnames_display)
        if d.where is not None:
            where_cells = resolve_where(
                d.where,
                data=table._data,
                group_positions=group_positions,
            )
            target_cells = [
                cell for cell in target_cells if (cell[0] + 1, cell[1] + 1) in where_cells
            ]
        values_before = {
            cell: _cell_value(cell, data_body, colnames_display) for cell in target_cells
        }
        generated_markup = _apply_digits(
            target_cells,
            d,
            data_body,
            typed_body,
            colnames_display,
            table._source_colnames,
            output,
        )
        _apply_fn(target_cells, d, data_body, colnames_display)
        _apply_replacements(
            target_cells, d, data_body, typed_body, colnames_display, table._source_colnames
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
            )
        )
        generated_markup.update(_apply_math(target_cells, d, data_body, colnames_display, output))
        intact_markup = {
            cell
            for cell, generated in generated_markup.items()
            if _cell_value(cell, data_body, colnames_display) == generated
        }
        escape_targets = [
            cell for cell in target_cells if cell not in intact_markup and cell not in escaped_cells
        ]
        explicitly_escaped = _apply_escapes(escape_targets, d, data_body, colnames_display, output)
        changed_cells = {
            cell
            for cell, before in values_before.items()
            if _cell_value(cell, data_body, colnames_display) != before
        }
        escaped_cells.difference_update(changed_cells)
        escaped_cells.update(intact_markup | explicitly_escaped)

    return escaped_cells
