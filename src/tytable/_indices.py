"""
Internal row/column index conventions and Typst conversion.

Convention (documented once, referenced everywhere):
- Data rows: 0-based (first data row is i=0)
- Column names header: i="header" maps to internal i=0
- Column-group headers: negative ints, i=-1 is topmost
- Columns: 0-based positions

Internal (1-based for Typst compatibility with nhead):
- nhead = (1 if show_colnames else 0) + len(col_groups)
- Data rows: 1-based positive (i=1 = first data row)
- Colnames: i=0
- Column-group headers: i<0 (i=-1 topmost)

Typst rows are 0-based for Typst's table model.
"""

from __future__ import annotations

import re
from collections.abc import Sequence


def convert_row_to_typst(i: int, nhead: int) -> int:
    """
    Convert an internal row index to a 0-based Typst row index.

    Internal convention: i=0 is colnames, i>=1 are data rows (1-based),
    i<0 are column-group header rows (i=-1 topmost). See module docstring.

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


def resolve_i(
    i: int | str | list[int] | None,
    *,
    nhead: int,
    group_positions: set[int],
    n_merged_body: int,
    has_header: bool,
) -> list[int] | None:
    """
    Resolve user row selector to internal row indices. guide 06 §1.

    Returns list[int], or None when i is None (caller decides the default).
    Internal convention: 0 = colnames, -k = col-group header (−1 topmost),
    1,2,... = data rows in the MERGED body.
    """
    if i is None:
        return None
    if isinstance(i, str):
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
    nums = i if isinstance(i, list) else [i]
    out = []
    for n in nums:
        if isinstance(n, str):
            raise TypeError("mixed str/int list not supported")
        if n < 0:
            if abs(n) > nhead - (1 if has_header else 0):
                raise ValueError(f"row selector {n} out of header range")
            out.append(n)
        else:
            out.append(n + 1)
    return out


def resolve_j(j: int | str | Sequence[int | str] | None, colnames: list[str]) -> list[int]:
    """Resolve user column selector to 1-based internal column indices. guide 06 §1."""
    if j is None:
        return list(range(1, len(colnames) + 1))
    if isinstance(j, (list, tuple)):
        if all(isinstance(x, str) for x in j):
            try:
                return [colnames.index(x) + 1 for x in j]
            except ValueError as e:
                raise ValueError(f"column name not found: {e}") from e
        return [int(x) + 1 for x in j]
    if isinstance(j, int):
        return [j + 1]
    if isinstance(j, str):
        if j in colnames:
            return [colnames.index(j) + 1]
        return [k + 1 for k, c in enumerate(colnames) if re.search(j, c)]
    raise TypeError(f"bad column selector: {j!r}")
