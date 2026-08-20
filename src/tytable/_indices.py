"""Resolve public selectors to final zero-based displayed cell coordinates."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import polars as pl
import polars.selectors as cs

from tytable._types import (
    _ColumnSelector,
    _GroupISelector,
    _GroupJSelector,
    _RegexSelector,
    _StyleRowSelector,
)

_MAX_REGEX_PATTERN_LENGTH = 500
RowKind = Literal["groupj", "header", "groupi", "data"]


@dataclass(frozen=True)
class RowLayout:
    """The table's resolved rows, expressed only in final display coordinates."""

    source_rows: int
    column_group_rows: int
    groupj_levels: tuple[int, ...]
    column_group_levels: int
    has_header: bool
    group_body_rows: frozenset[int]
    groupi_labels: tuple[str | None, ...]
    source_body_rows: tuple[int, ...]

    @classmethod
    def create(
        cls,
        *,
        source_rows: int,
        column_group_rows: int,
        groupj_levels: Sequence[int] | None = None,
        column_group_levels: int | None = None,
        has_header: bool,
        group_body_rows: set[int],
        groupi_labels: Sequence[str] | None = None,
    ) -> RowLayout:
        body_rows = source_rows + len(group_body_rows)
        source_body_rows = tuple(r for r in range(body_rows) if r not in group_body_rows)
        if len(source_body_rows) != source_rows:
            raise ValueError("row-group positions do not describe a valid body layout")
        resolved_groupi_labels: tuple[str | None, ...] = (
            (None,) * len(group_body_rows) if groupi_labels is None else tuple(groupi_labels)
        )
        if len(resolved_groupi_labels) != len(group_body_rows):
            raise ValueError("groupi labels must contain one entry per row-group separator")
        resolved_levels = (
            tuple(reversed(range(column_group_rows)))
            if groupj_levels is None
            else tuple(groupj_levels)
        )
        if len(resolved_levels) != column_group_rows:
            raise ValueError("groupj levels must contain one entry per displayed column-group row")
        total_levels = column_group_rows if column_group_levels is None else column_group_levels
        if total_levels < column_group_rows:
            raise ValueError("column-group level count cannot be smaller than its displayed rows")
        if len(set(resolved_levels)) != len(resolved_levels) or any(
            level < 0 or level >= total_levels for level in resolved_levels
        ):
            raise ValueError("groupj levels must be unique valid semantic level indices")
        return cls(
            source_rows=source_rows,
            column_group_rows=column_group_rows,
            groupj_levels=resolved_levels,
            column_group_levels=total_levels,
            has_header=has_header,
            group_body_rows=frozenset(group_body_rows),
            groupi_labels=resolved_groupi_labels,
            source_body_rows=source_body_rows,
        )

    @property
    def header_rows(self) -> int:
        return self.column_group_rows + int(self.has_header)

    @property
    def body_rows(self) -> int:
        return self.source_rows + len(self.group_body_rows)

    @property
    def total_rows(self) -> int:
        return self.header_rows + self.body_rows

    @property
    def groupj_rows(self) -> tuple[int, ...]:
        return tuple(range(self.column_group_rows))

    def groupj_level(self, display_row: int) -> int:
        """Return the stable semantic level for a displayed column-group row."""
        if display_row < 0 or display_row >= self.column_group_rows:
            raise ValueError(f"display row {display_row} is not a column-group row")
        return self.groupj_levels[display_row]

    @property
    def header_row(self) -> int | None:
        return self.column_group_rows if self.has_header else None

    @property
    def groupi_rows(self) -> tuple[int, ...]:
        return tuple(self.header_rows + r for r in sorted(self.group_body_rows))

    @property
    def data_rows(self) -> tuple[int, ...]:
        return tuple(self.header_rows + r for r in self.source_body_rows)

    @property
    def first_row(self) -> int | None:
        return 0 if self.total_rows else None

    @property
    def last_row(self) -> int | None:
        return self.total_rows - 1 if self.total_rows else None

    def source_to_display(self, row: int) -> int:
        return self.header_rows + self.source_body_rows[row]

    def body_index(self, display_row: int) -> int:
        body_row = display_row - self.header_rows
        if body_row < 0 or body_row >= self.body_rows:
            raise ValueError(f"display row {display_row} is not a body row")
        return body_row

    def kind(self, display_row: int) -> RowKind:
        if display_row < 0 or display_row >= self.total_rows:
            raise ValueError(f"display row {display_row} is outside the table")
        if display_row < self.column_group_rows:
            return "groupj"
        if self.has_header and display_row == self.column_group_rows:
            return "header"
        return "groupi" if self.body_index(display_row) in self.group_body_rows else "data"

    def require_supported(self, rows: Sequence[int], *, allowed: set[RowKind], method: str) -> None:
        unsupported = sorted({self.kind(row) for row in rows} - allowed)
        if unsupported:
            kinds = ", ".join(repr(kind) for kind in unsupported)
            raise ValueError(f"{method} cannot target row kind(s): {kinds}")

    def resolve_string(self, selector: str) -> list[int]:
        if selector == "header":
            return [] if self.header_row is None else [self.header_row]
        if selector == "groupi":
            return list(self.groupi_rows)
        if selector == "data":
            return list(self.data_rows)
        if selector == "groupj":
            return list(self.groupj_rows)
        if selector == "all":
            return list(range(self.total_rows))
        raise ValueError(f"unknown row selector: {selector!r}")

    def resolve_groupj(self, selector: _GroupJSelector) -> list[int]:
        """Resolve a typed column-group selector without renumbering hidden levels."""
        if selector.level is None:
            return list(self.groupj_rows)
        if selector.level >= self.column_group_levels:
            raise ValueError(
                f"column-group level {selector.level} is out of range for "
                f"{self.column_group_levels} level(s)"
            )
        return [
            display_row
            for display_row, level in enumerate(self.groupj_levels)
            if level == selector.level
        ]

    def resolve_groupi(self, selector: _GroupISelector) -> list[int]:
        """Resolve a typed row-group selector against original registered labels."""
        if selector.label is None:
            return list(self.groupi_rows)
        matches = [
            display_row
            for display_row, label in zip(self.groupi_rows, self.groupi_labels, strict=True)
            if label == selector.label
        ]
        if not matches:
            raise ValueError(f"row-group label matched no groups: {selector.label!r}")
        return matches


def resolve_i(
    i: _StyleRowSelector,
    *,
    layout: RowLayout,
    data: pl.DataFrame | None = None,
) -> list[int]:
    """Resolve a public row selector to canonical final display rows."""

    def source_to_display(rows: list[int]) -> list[int]:
        return [layout.source_to_display(row) for row in rows]

    if i is None:
        return list(layout.data_rows)

    sequence = i if isinstance(i, Sequence) and not isinstance(i, (str, bytes, bytearray)) else None

    if (
        sequence is not None
        and len(sequence) > 0
        and any(isinstance(value, bool) for value in sequence)
    ):
        if not all(isinstance(value, bool) for value in sequence):
            raise TypeError("boolean row masks cannot mix booleans with other selector types")
        if data is None:
            raise TypeError("boolean row masks require source data")
        if len(sequence) != data.height:
            raise ValueError(
                f"boolean row mask has length {len(sequence)}, expected {data.height} source rows"
            )
        return source_to_display([j for j, value in enumerate(sequence) if value])

    if data is not None:
        if isinstance(i, pl.Expr):
            selected = data.select(i)
            if selected.width != 1:
                raise ValueError(
                    f"row selector expression must produce one column, got {selected.width}"
                )
            mask = selected.to_series()
            if mask.dtype != pl.Boolean:
                raise TypeError(
                    f"row selector expression must produce Boolean values, got {mask.dtype}"
                )
            if len(mask) != data.height:
                raise ValueError(
                    f"row selector expression returned {len(mask)} value(s), expected "
                    f"{data.height} source rows"
                )
            return source_to_display([j for j, value in enumerate(mask) if value])
        if isinstance(i, pl.Series):
            if i.dtype != pl.Boolean:
                raise TypeError(f"row mask Series must have Boolean dtype, got {i.dtype}")
            if len(i) != data.height:
                raise ValueError(
                    f"boolean row mask has length {len(i)}, expected {data.height} source rows"
                )
            return source_to_display([j for j, value in enumerate(i) if value])
        if callable(i) and not isinstance(i, (int, str)):
            return source_to_display(
                [j for j, row in enumerate(data.iter_rows(named=True)) if i(row)]
            )

    if isinstance(i, str):
        return layout.resolve_string(i)

    if isinstance(i, _GroupJSelector):
        return layout.resolve_groupj(i)

    if isinstance(i, _GroupISelector):
        return layout.resolve_groupi(i)

    if sequence is not None:
        rows: list[int] = []
        for value in sequence:
            if isinstance(value, str):
                rows.extend(layout.resolve_string(value))
            elif isinstance(value, _GroupJSelector):
                rows.extend(layout.resolve_groupj(value))
            elif isinstance(value, _GroupISelector):
                rows.extend(layout.resolve_groupi(value))
            elif isinstance(value, int):
                if isinstance(value, bool):
                    raise TypeError(
                        "boolean row masks cannot mix booleans with other selector types"
                    )
                _validate_source_row(value, layout.source_rows)
                rows.append(layout.source_to_display(value))
            else:
                raise TypeError(f"unsupported element type in row list: {type(value).__name__}")
        return sorted(set(rows))

    if isinstance(i, int):
        if isinstance(i, bool):
            raise TypeError("bad row selector type: bool")
        _validate_source_row(i, layout.source_rows)
        return [layout.source_to_display(i)]

    raise TypeError(f"bad row selector type: {type(i).__name__}")


def _validate_source_row(row: int, source_rows: int) -> None:
    if row < 0:
        raise ValueError("negative row selectors are not supported")
    if row >= source_rows:
        raise ValueError(
            f"row selector position {row} out of range for {source_rows} source row(s)"
        )


def resolve_j(
    j: _ColumnSelector,
    data: pl.DataFrame,
) -> list[int]:
    """Resolve a public column selector to zero-based column indices."""
    colnames = data.columns
    if j is None:
        return list(range(len(colnames)))
    if cs.is_selector(j):
        return _resolve_selector_j(j, data)
    if isinstance(j, Sequence) and not isinstance(j, (str, bytes, bytearray)):
        result: list[int] = []
        for value in j:
            resolved = _resolve_single_j(value, data)
            for idx in resolved:
                if idx not in result:
                    result.append(idx)
        return sorted(result)
    if isinstance(j, (int, str, _RegexSelector)):
        return _resolve_single_j(j, data)
    raise TypeError(f"bad column selector: {j!r}")


def _resolve_single_j(value: object, data: pl.DataFrame) -> list[int]:
    colnames = data.columns
    if cs.is_selector(value):
        return _resolve_selector_j(value, data)
    if isinstance(value, bool):
        raise TypeError(
            "column selector elements must be integers, strings, regex selectors, or Polars "
            "selectors, got bool"
        )
    if isinstance(value, int):
        if value < 0 or value >= len(colnames):
            raise ValueError(
                f"column selector position {value} out of range for {len(colnames)} column(s)"
            )
        return [value]
    if isinstance(value, _RegexSelector):
        return _resolve_regex(value.pattern, colnames)
    if isinstance(value, str):
        if value in colnames:
            return [colnames.index(value)]
        raise ValueError(f"column not found: {value!r}")
    raise TypeError(
        "column selector elements must be integers, strings, regex selectors, or Polars "
        f"selectors, got {type(value).__name__}"
    )


def _resolve_selector_j(selector: pl.Expr, data: pl.DataFrame) -> list[int]:
    """Expand a Polars column selector against the stable source schema."""
    selected = data.select(selector).columns
    positions = {name: idx for idx, name in enumerate(data.columns)}
    return [positions[name] for name in selected]


def resolve_where(
    where: pl.Expr,
    *,
    data: pl.DataFrame,
    layout: RowLayout,
) -> set[tuple[int, int]]:
    """Resolve a Polars expression to final displayed cell coordinates."""
    if not isinstance(where, pl.Expr):
        raise TypeError(f"where must be a Polars expression, got {type(where).__name__}")

    mask = data.select(where)
    if mask.width == 0:
        return set()
    if mask.height != data.height:
        raise ValueError(
            f"where expression returned {mask.height} row(s) for a {data.height}-row table"
        )

    source_positions = {name: j for j, name in enumerate(data.columns)}
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
        display_rows = [layout.source_to_display(row) for row in selected_rows]
        cells.update((row, source_positions[name]) for row in display_rows)
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
    result = [k for k, c in enumerate(colnames) if compiled.search(c)]
    if not result:
        raise ValueError(f"regex matched no columns: {pattern!r}")
    return result
