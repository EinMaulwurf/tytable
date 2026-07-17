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
        elif isinstance(c, bool):
            raise TypeError("column spec must be str or int, got bool")
        elif isinstance(c, int):
            if c < 0 or c >= len(colnames):
                raise IndexError(
                    f"column group position {c} is out of range for {len(colnames)} columns"
                )
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
    claimed: set[int] = set()
    for label, cols in j_dict.items():
        if label is None:
            raise ValueError("column group labels must not be None")
        if not isinstance(cols, list):
            raise TypeError(
                f"columns for column group {label!r} must be a list, got {type(cols).__name__}"
            )
        indices = _resolve_cols(cols, colnames)
        if not indices:
            raise ValueError(f"column group {label!r} must select at least one column")
        if len(indices) != len(set(indices)):
            raise ValueError(f"column group {label!r} contains duplicate columns")
        expected = list(range(indices[0], indices[0] + len(indices)))
        if indices != expected:
            raise ValueError(f"column group {label!r} must select a contiguous span in order")
        overlap = claimed.intersection(indices)
        if overlap:
            raise ValueError(
                f"column group {label!r} overlaps another group at column {min(overlap)}"
            )
        claimed.update(indices)
        start = indices[0]
        row[start] = str(label)
        for ci in indices[1:]:
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
        positions: set[int] = set()
        for label, pos in i.items():
            if label is None:
                raise ValueError("row group labels must not be None")
            if isinstance(pos, bool) or not isinstance(pos, int):
                raise TypeError(
                    f"row group position for {label!r} must be an integer, got {type(pos).__name__}"
                )
            if pos < 0 or pos > table._data.height:
                raise IndexError(
                    f"row group position {pos} is out of range for {table._data.height} rows"
                )
            if pos in positions:
                raise ValueError(f"multiple row groups cannot use position {pos}")
            positions.add(pos)
        pairs = sorted(i.items(), key=lambda x: x[1])
        for label, pos in pairs:
            table._row_groups.append(RowGroup(label=str(label), position=pos))
    elif isinstance(i, list):
        if len(i) != table._data.height:
            raise ValueError(
                f"row group list must contain exactly {table._data.height} entries, got {len(i)}"
            )
        if any(label is None for label in i):
            raise ValueError("row group labels must not be None")
        prev = None
        pos = 0
        for idx, val in enumerate(i):
            if idx > 0 and val != prev:
                table._row_groups.append(RowGroup(label=str(prev), position=pos))
                pos = idx
            prev = val
        if pos < len(i):
            table._row_groups.append(RowGroup(label=str(prev), position=pos))
    else:
        raise TypeError("group(i=...) must be a dict or list")
    return table


def register_col_groups(
    table: TyTable, j: dict[str, list[str | int]], colnames: list[str]
) -> TyTable:
    """Record a column-group header row from a ``{label: [cols]}`` dict."""
    if isinstance(j, dict):
        if not j:
            return table
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
