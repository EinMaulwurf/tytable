"""
Internal row/column index conventions and Typst conversion.

Convention (documented once, referenced everywhere):
- Data rows: 0-based (first data row is i=0)
- Column names header: i="header" maps to internal i=0
- Column-group headers: negative ints, i=-1 is innermost (nearest colnames)
- Columns: 0-based positions

Internal (1-based for Typst compatibility with nhead):
- nhead = (1 if show_colnames else 0) + len(col_groups)
- Data rows: 1-based positive (i=1 = first data row)
- Colnames: i=0
- Column-group headers: i<0 (i=-1 innermost; decreasing values move upward)

Typst rows are 0-based for Typst's table model.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

import polars as pl

_MAX_REGEX_PATTERN_LENGTH = 500


def convert_row_to_typst(i: int, nhead: int) -> int:
    """
    Convert an internal row index to a 0-based Typst row index.

    Internal convention: i=0 is colnames, i>=1 are data rows (1-based),
    i<0 are column-group header rows (i=-1 innermost). See module docstring.

    nhead=3 examples: -2->0, -1->1, 0->2, 1->3, 2->4.
    nhead=1 examples: 0->0, 1->1, 2->2.
    nhead=0 examples: 1->0.
    """
    if nhead > 0:
        if i < 0:
            return nhead + i - 1
        return i + nhead - 1
    if i <= 0:
        raise ValueError(f"row index {i} invalid when nhead == 0")
    return i - 1


def convert_col_to_typst(j: int) -> int:
    """Convert a 1-based internal column index to a 0-based Typst column index."""
    return j - 1


def _map_original_to_internal(orig_indices: list[int], group_positions: set[int]) -> list[int]:
    """Map 0-based original row indices to 1-based internal indices accounting for row groups."""
    if not group_positions:
        return [i + 1 for i in orig_indices]
    groups = sorted(group_positions)
    result: list[int] = []
    for orig in sorted(orig_indices):
        internal = orig + 1
        for gp in groups:
            if gp <= internal:
                internal += 1
        result.append(internal)
    return result


def _resolve_str_i(
    i: str,
    *,
    nhead: int,
    group_positions: set[int],
    n_merged_body: int,
    has_header: bool,
) -> list[int]:
    """Resolve a single string row selector."""
    if i == "header":
        return [0] if has_header else []
    if i == "groupi":
        return sorted(group_positions)
    if i == "~groupi":
        return [r for r in range(1, n_merged_body + 1) if r not in group_positions]
    if i == "groupj":
        return list(range(-(nhead - 1), 0)) if nhead else []
    if i == "body":
        return list(range(1, n_merged_body + 1))
    if i == "all":
        hdr = ([0] if has_header else []) + (list(range(-(nhead - 1), 0)) if nhead > 1 else [])
        return hdr + list(range(1, n_merged_body + 1))
    raise ValueError(f"unknown row selector: {i!r}")


def resolve_i(
    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None,
    *,
    nhead: int,
    group_positions: set[int],
    n_merged_body: int,
    has_header: bool,
    data: pl.DataFrame | None = None,
) -> list[int] | None:
    """
    Resolve user row selector to internal row indices. guide 06 §1.

    Returns list[int], or None when i is None (caller decides the default).
    Internal convention: 0 = colnames, -k = col-group header (−1 innermost),
    1,2,... = data rows in the MERGED body.

    Data-driven selectors (``pl.Expr``, boolean ``pl.Series``, or
    ``callable(row) -> bool``) are evaluated against *data* and mapped
    through row-group positions.
    """
    if i is None:
        return None

    if data is not None:
        if isinstance(i, pl.Expr):
            mask = data.select(i).to_series()
            orig_indices = [j for j, v in enumerate(mask) if v]
            return _map_original_to_internal(orig_indices, group_positions)
        if isinstance(i, pl.Series):
            orig_indices = [j for j, v in enumerate(i) if v]
            return _map_original_to_internal(orig_indices, group_positions)
        if callable(i) and not isinstance(i, (int, str)):
            orig_indices = [j for j, row in enumerate(data.iter_rows(named=True)) if i(row)]
            return _map_original_to_internal(orig_indices, group_positions)

    if isinstance(i, str):
        return _resolve_str_i(
            i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
        )

    if isinstance(i, (list, tuple)):
        out: list[int] = []
        for n in i:
            if isinstance(n, str):
                resolved = _resolve_str_i(
                    n,
                    nhead=nhead,
                    group_positions=group_positions,
                    n_merged_body=n_merged_body,
                    has_header=has_header,
                )
                out.extend(resolved)
            elif isinstance(n, int):
                if n < 0:
                    if abs(n) > nhead - (1 if has_header else 0):
                        raise ValueError(f"row selector {n} out of header range")
                    out.append(n)
                else:
                    out.append(n + 1)
            else:
                raise TypeError(f"unsupported element type in row list: {type(n).__name__}")
        return out

    if isinstance(i, int):
        if i < 0:
            if abs(i) > nhead - (1 if has_header else 0):
                raise ValueError(f"row selector {i} out of header range")
            return [i]
        return [i + 1]

    raise TypeError(f"bad row selector type: {type(i).__name__}")


def resolve_j(
    j: int | str | Sequence[int | str] | None,
    colnames: list[str],
    *,
    regex: bool = False,
) -> list[int]:
    """Resolve user column selector to 1-based internal column indices. guide 06 §1."""
    if j is None:
        return list(range(1, len(colnames) + 1))
    if isinstance(j, (list, tuple)):
        if all(isinstance(x, str) for x in j):
            if regex:
                return _resolve_regex_list(j, colnames)
            try:
                return [colnames.index(x) + 1 for x in j]
            except ValueError as e:
                raise ValueError(f"column name not found: {e}") from e
        return [int(x) + 1 for x in j]
    if isinstance(j, int):
        return [j + 1]
    if isinstance(j, str):
        if regex:
            return _resolve_regex(j, colnames)
        if j in colnames:
            return [colnames.index(j) + 1]
        raise ValueError(f"column not found: {j!r}")
    raise TypeError(f"bad column selector: {j!r}")


def resolve_where(
    where: pl.Expr,
    *,
    data: pl.DataFrame,
    group_positions: set[int],
) -> set[tuple[int, int]]:
    """Resolve a Polars expression to internal body-cell coordinates.

    Each boolean output column is matched to the source column with the same
    name. True values select individual cells; false and null values do not.
    """
    if not isinstance(where, pl.Expr):
        raise TypeError(f"where must be a Polars expression, got {type(where).__name__}")

    mask = data.select(where)
    if mask.width == 0:
        return set()
    if mask.height != data.height:
        raise ValueError(
            f"where expression returned {mask.height} row(s) for a {data.height}-row table"
        )

    source_positions = {name: j + 1 for j, name in enumerate(data.columns)}
    unknown = [name for name in mask.columns if name not in source_positions]
    if unknown:
        raise ValueError(
            "where expression output column(s) do not match source columns: "
            + ", ".join(repr(name) for name in unknown)
        )

    non_boolean = [name for name, dtype in mask.schema.items() if dtype != pl.Boolean]
    if non_boolean:
        raise TypeError(
            "where expression must produce boolean columns; got non-boolean column(s): "
            + ", ".join(repr(name) for name in non_boolean)
        )

    cells: set[tuple[int, int]] = set()
    for name in mask.columns:
        selected_rows = [i for i, value in enumerate(mask[name]) if value is True]
        internal_rows = _map_original_to_internal(selected_rows, group_positions)
        j = source_positions[name]
        cells.update((i, j) for i in internal_rows)
    return cells


def _resolve_regex(pattern: str, colnames: list[str]) -> list[int]:
    if len(pattern) > _MAX_REGEX_PATTERN_LENGTH:
        raise ValueError(
            "regex pattern is too long: "
            f"{len(pattern)} characters (maximum {_MAX_REGEX_PATTERN_LENGTH})"
        )
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"invalid regex pattern: {pattern!r} ({e})") from e
    result = [k + 1 for k, c in enumerate(colnames) if compiled.search(c)]
    if not result:
        raise ValueError(f"regex matched no columns: {pattern!r}")
    return result


def _resolve_regex_list(patterns: Sequence[str], colnames: list[str]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for pat in patterns:
        for idx in _resolve_regex(pat, colnames):
            if idx not in seen:
                seen.add(idx)
                result.append(idx)
    if not result:
        raise ValueError(f"regex patterns matched no columns: {patterns!r}")
    return result
