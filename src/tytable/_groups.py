"""
Row and column group registration and merging into the table body.

Called by :meth:`TyTable.group` to record groups, and by
:func:`tytable._resolve.build` to merge row-group separator rows into the body.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import polars as pl
import polars.selectors as cs

from ._directives import RowGroup
from ._indices import resolve_j
from ._types import _ColGroupSelector, _ColumnSelectorSpec, _RegexSelector

if TYPE_CHECKING:
    from ._tytable import TyTable


def _resolve_cols(
    col_spec: _ColumnSelectorSpec,
    data: pl.DataFrame,
    column_group_rows: Sequence[Sequence[str | None]] = (),
) -> list[int]:
    """Translate a list of column names/positions into 0-based integer indices."""
    if cs.is_selector(col_spec) or isinstance(col_spec, (_RegexSelector, _ColGroupSelector)):
        return resolve_j(col_spec, data, column_group_rows=column_group_rows)
    if isinstance(col_spec, (str, bytes)) or not isinstance(col_spec, Sequence):
        raise TypeError(
            "column spec must be a sequence, regex selector, column-group selector, "
            "or Polars selector, "
            f"got {type(col_spec).__name__}"
        )

    colnames = data.columns
    indices = []
    for c in col_spec:
        if cs.is_selector(c) or isinstance(c, (_RegexSelector, _ColGroupSelector)):
            indices.extend(resolve_j(c, data, column_group_rows=column_group_rows))
        elif isinstance(c, str):
            try:
                indices.append(colnames.index(c))
            except ValueError:
                raise ValueError(f"column {c!r} not found") from None
        elif isinstance(c, bool):
            raise TypeError("column spec must be str or int, got bool")
        elif isinstance(c, int):
            if c < 0 or c >= len(colnames):
                raise ValueError(
                    f"column group position {c} is out of range for {len(colnames)} columns"
                )
            indices.append(c)
        else:
            raise TypeError(
                "column spec must be str, int, regex selector, column-group selector, "
                "or Polars selector, "
                f"got {type(c).__name__}"
            )
    return indices


def _display_group_label(label: object) -> str:
    """Return a nonempty display string for one registered group label."""
    if label is None:
        raise ValueError("group labels must not be None")
    display_label = str(label)
    if not display_label.strip():
        raise ValueError("group labels must not be empty")
    return display_label


def _build_col_group_row(
    j_dict: Mapping[Any, _ColumnSelectorSpec],
    data: pl.DataFrame,
    column_group_rows: Sequence[Sequence[str | None]] = (),
) -> list[str | None]:
    """Build one column-group header row (label at span start, ``""`` under the span, ``None`` elsewhere)."""
    colnames = data.columns
    ncol = len(colnames)
    row: list[str | None] = [None] * ncol
    claimed: set[int] = set()
    for label, cols in j_dict.items():
        display_label = _display_group_label(label)
        indices = _resolve_cols(cols, data, column_group_rows)
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
        row[start] = display_label
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


def register_row_groups(table: TyTable, i: Mapping[Any, int] | Sequence[Any]) -> TyTable:
    """Record row-group separators from a mapping or a run-length sequence."""
    groups: list[RowGroup] = []
    if isinstance(i, Mapping):
        normalized: list[tuple[str, int]] = []
        for label, pos in i.items():
            display_label = _display_group_label(label)
            if isinstance(pos, bool) or not isinstance(pos, int):
                raise TypeError(
                    f"row group position for {label!r} must be an integer, got {type(pos).__name__}"
                )
            if pos < 0 or pos > table._data.height:
                raise ValueError(
                    f"row group position {pos} is out of range for {table._data.height} rows"
                )
            normalized.append((display_label, pos))
        for label, pos in sorted(normalized, key=lambda x: x[1]):
            groups.append(RowGroup(label=label, position=pos))
    elif not isinstance(i, (str, bytes)) and isinstance(i, Sequence):
        if len(i) != table._data.height:
            raise ValueError(
                f"row group list must contain exactly {table._data.height} entries, got {len(i)}"
            )
        labels = [_display_group_label(label) for label in i]
        prev = None
        pos = 0
        for idx, val in enumerate(labels):
            if idx > 0 and val != prev:
                groups.append(RowGroup(label=str(prev), position=pos))
                pos = idx
            prev = val
        if pos < len(i):
            groups.append(RowGroup(label=str(prev), position=pos))
    else:
        raise TypeError("group(i=...) must be a mapping or sequence")

    positions = {group.position for group in table._row_groups}
    for group in groups:
        if group.position in positions:
            raise ValueError(f"multiple row groups cannot use position {group.position}")
        positions.add(group.position)
    table._row_groups.extend(groups)
    return table


def register_col_groups(table: TyTable, j: Mapping[Any, _ColumnSelectorSpec]) -> TyTable:
    """Record a column-group header row from a ``{label: [cols]}`` mapping."""
    if isinstance(j, Mapping):
        if not j:
            return table
        row = _build_col_group_row(j, table._data, table._col_group_rows)
        table._col_group_rows.insert(0, row)
    else:
        raise TypeError("group(j=...) must be a mapping")
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
    """Interleave row-group rows; return zero-based body positions and labels."""
    if not row_groups:
        return data_body, {}
    nrows = len(data_body)
    ngroups = len(row_groups)
    n_merged = nrows + ngroups
    p = sorted(rg.position for rg in row_groups)
    group_positions = [p[k] + k for k in range(ngroups)]
    group_positions_set = set(group_positions)
    sorted_rg = sorted(row_groups, key=lambda rg: rg.position)
    pos_to_label = dict(zip(group_positions, (rg.label for rg in sorted_rg), strict=True))
    merged = []
    data_row_idx = 0
    for r in range(n_merged):
        if r in group_positions_set:
            merged.append([pos_to_label[r]] + [""] * (ncols - 1))
        else:
            merged.append(data_body[data_row_idx])
            data_row_idx += 1
    return merged, pos_to_label
