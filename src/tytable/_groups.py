"""
Row and column group registration and merging into the table body.

Called by :meth:`TyTable.group` to record groups, and by
:func:`tytable._resolve.build` to merge row-group separator rows into the body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._directives import RowGroup

if TYPE_CHECKING:
    from ._tytable import TyTable


def _resolve_cols(col_spec: list[str | int], colnames: list[str]) -> list[int]:
    """Translate a list of column names/positions into 0-based integer indices."""
    indices = []
    for c in col_spec:
        if isinstance(c, str):
            try:
                indices.append(colnames.index(c))
            except ValueError:
                raise ValueError(f"column {c!r} not found") from None
        elif isinstance(c, int):
            indices.append(c)
        else:
            raise TypeError(f"column spec must be str or int, got {type(c).__name__}")
    return indices


def _build_col_group_row(
    j_dict: dict[str, list[str | int]], colnames: list[str]
) -> list[str | None]:
    """Build one column-group header row (label at span start, ``""`` under the span, ``None`` elsewhere)."""
    ncol = len(colnames)
    row: list[str | None] = [None] * ncol
    for label, cols in j_dict.items():
        indices = _resolve_cols(cols, colnames)
        if not indices:
            continue
        start = indices[0]
        row[start] = label
        for ci in indices[1:]:
            if 0 <= ci < ncol:
                row[ci] = ""
    return row


def _build_col_group_rows_delim(delim: str, colnames: list[str]) -> list[list[str | None]]:
    """Split column names on ``delim`` and build one header row per hierarchical level."""
    if not delim:
        raise ValueError("delimiter must not be empty")
    parts = [c.split(delim) for c in colnames]
    if not parts or any(len(p) == 1 for p in parts):
        raise ValueError(f"delimiter {delim!r} must occur in every column name")
    nlevels = len(parts[0])
    if any(len(p) != nlevels for p in parts):
        raise ValueError(
            f"delimiter {delim!r} does not split all column names into the same number of parts"
        )
    rows: list[list[str | None]] = []
    for level in range(nlevels):
        ncol = len(colnames)
        row: list[str | None] = [None] * ncol
        i = 0
        while i < ncol:
            label = parts[i][level].strip()
            start = i
            i += 1
            while i < ncol and parts[i][level].strip() == label:
                i += 1
            display = label if label else " "
            row[start] = display
            for ci in range(start + 1, i):
                row[ci] = ""
        rows.append(row)
    return rows


def _resolve_col_group_spans(row: list[str | None]) -> list[tuple[str, int, int]]:
    """Return ``(label, start, span)`` entries for a column-group header row.

    An empty string immediately after a label extends that label's span, while
    ``None`` and standalone empty strings each represent one blank cell.
    """
    spans: list[tuple[str, int, int]] = []
    i = 0
    while i < len(row):
        value = row[i]
        label = "" if value is None else value.strip()
        start = i
        i += 1
        if label:
            while i < len(row) and row[i] is not None and (row[i] or "").strip() == "":
                i += 1
        spans.append((label, start, i - start))
    return spans


def register_row_groups(table: TyTable, i: dict[str, int] | list[Any]) -> TyTable:
    """Record row-group separators from a ``{label: row}`` dict or a run-length list."""
    if isinstance(i, dict):
        pairs = sorted(i.items(), key=lambda x: x[1])
        for label, pos in pairs:
            table._row_groups.append(RowGroup(label=str(label), position=int(pos)))
    elif isinstance(i, list):
        prev = None
        pos = 0
        for idx, val in enumerate(i):
            if idx > 0 and val != prev:
                table._row_groups.append(RowGroup(label=str(prev), position=pos))
                pos = idx
            prev = val
        if pos < len(i) and prev is not None:
            table._row_groups.append(RowGroup(label=str(prev), position=pos))
    else:
        raise TypeError("group(i=...) must be a dict or list")
    return table


def register_col_groups(
    table: TyTable, j: dict[str, list[str | int]], colnames: list[str]
) -> TyTable:
    """Record a column-group header row from a ``{label: [cols]}`` dict."""
    if isinstance(j, dict):
        row = _build_col_group_row(j, colnames)
        table._col_group_rows.insert(0, row)
    else:
        raise TypeError("group(j=...) must be a dict")
    return table


def register_delimiter_groups(table: TyTable, delimiter: str, colnames: list[str]) -> TyTable:
    """Record hierarchical column-group rows derived from a column-name delimiter."""
    if not isinstance(delimiter, str):
        raise TypeError("group(delimiter=...) must be a str")
    rows = _build_col_group_rows_delim(delimiter, colnames)
    for row in reversed(rows):
        table._col_group_rows.insert(0, row)
    return table


def merge_row_groups(
    data_body: list[list[str]], row_groups: list[RowGroup], ncols: int
) -> tuple[list[list[str]], dict[int, str]]:
    """Interleave row-group separator rows into the body; returns the merged body and ``{row: label}``."""
    if not row_groups:
        return data_body, {}
    nrows = len(data_body)
    ngroups = len(row_groups)
    n_merged = nrows + ngroups
    p = sorted(rg.position for rg in row_groups)
    group_positions_1 = [p[k] + k + 1 for k in range(ngroups)]
    group_positions_set = set(group_positions_1)
    sorted_rg = sorted(row_groups, key=lambda rg: rg.position)
    pos_to_label = dict(zip(group_positions_1, (rg.label for rg in sorted_rg), strict=True))
    merged = []
    data_row_idx = 0
    for r in range(1, n_merged + 1):
        if r in group_positions_set:
            merged.append([pos_to_label[r]] + [""] * (ncols - 1))
        else:
            merged.append(data_body[data_row_idx])
            data_row_idx += 1
    return merged, pos_to_label
