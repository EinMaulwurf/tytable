"""
Value formatting: digits, significant figures, replace, escape, and fn transforms.

Applied during the render pipeline by :func:`tytable._resolve.build`.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ._escape import escape_typst
from ._indices import resolve_i, resolve_j

if TYPE_CHECKING:
    from ._tytable import TinyTable


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
        if output in ("html", "ascii"):
            from ._escape import escape_html

            return escape_html(current_str)
        return escape_typst(current_str)
    return current_str


def apply_formats(
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    table: TinyTable,
    *,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
    output: str,
    colnames: list[str],
) -> set[tuple[int, int]]:
    """Apply every ``FormatDirective`` to the data body, returning cells that were explicitly escaped."""
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
        ) or resolve_i(
            "body",
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
        )
        assert i_vals is not None
        j_vals = resolve_j(d.j, colnames)

        target_cells: list[tuple[int, int]] = []
        for i_idx in i_vals:
            row_idx = i_idx - 1
            if row_idx < 0 or row_idx >= len(data_body):
                continue
            for j_idx in j_vals:
                col_idx = j_idx - 1
                if col_idx < 0 or col_idx >= len(data_body[row_idx]):
                    continue
                target_cells.append((row_idx, col_idx))

        if d.digits is not None:
            for row_idx, col_idx in target_cells:
                if row_idx < len(typed_body) and col_idx < len(typed_body[row_idx]):
                    typed_val = typed_body[row_idx][col_idx]
                else:
                    typed_val = None
                if _is_numeric_typed(typed_val) and not isinstance(typed_val, int):
                    num_fmt = d.num_fmt or "decimal"
                    if num_fmt == "significant":
                        data_body[row_idx][col_idx] = _fmt_numeric_significant(typed_val, d.digits)
                    else:
                        data_body[row_idx][col_idx] = _fmt_numeric_decimal(typed_val, d.digits)

        if d.fn is not None:
            col_to_rows: dict[int, list[int]] = {}
            for row_idx, col_idx in target_cells:
                col_to_rows.setdefault(col_idx, []).append(row_idx)
            for col_idx, rows in col_to_rows.items():
                sorted_rows = sorted(rows)
                vec = [data_body[r][col_idx] for r in sorted_rows]
                result = d.fn(vec)
                if len(result) != len(vec):
                    raise ValueError(f"fn() returned {len(result)} items, expected {len(vec)}")
                for r, val in zip(sorted_rows, result, strict=True):
                    data_body[r][col_idx] = str(val)

        if d.replace is not None:
            for row_idx, col_idx in target_cells:
                if row_idx < len(typed_body) and col_idx < len(typed_body[row_idx]):
                    typed_val = typed_body[row_idx][col_idx]
                else:
                    typed_val = None
                current = data_body[row_idx][col_idx]
                data_body[row_idx][col_idx] = _apply_replace(typed_val, current, d.replace)

        if d.escape:
            for row_idx, col_idx in target_cells:
                current = data_body[row_idx][col_idx]
                data_body[row_idx][col_idx] = _apply_escape(current, d.escape, output)
                escaped_cells.add((row_idx, col_idx))

    return escaped_cells
