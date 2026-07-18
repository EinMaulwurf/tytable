"""Resolve public selectors to final zero-based displayed cell coordinates."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

import polars as pl

_MAX_REGEX_PATTERN_LENGTH = 500
RowKind = Literal["groupj", "header", "groupi", "data"]


@dataclass(frozen=True)
class RowLayout:
    """The table's resolved rows, expressed only in final display coordinates."""

    source_rows: int
    column_group_rows: int
    has_header: bool
    group_body_rows: frozenset[int]
    source_body_rows: tuple[int, ...]

    @classmethod
    def create(
        cls,
        *,
        source_rows: int,
        column_group_rows: int,
        has_header: bool,
        group_body_rows: set[int],
    ) -> RowLayout:
        body_rows = source_rows + len(group_body_rows)
        source_body_rows = tuple(r for r in range(body_rows) if r not in group_body_rows)
        if len(source_body_rows) != source_rows:
            raise ValueError("row-group positions do not describe a valid body layout")
        return cls(
            source_rows=source_rows,
            column_group_rows=column_group_rows,
            has_header=has_header,
            group_body_rows=frozenset(group_body_rows),
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


def resolve_i(
    i: int | str | Sequence[int | str] | pl.Expr | pl.Series | Callable[[dict], bool] | None,
    *,
    layout: RowLayout,
    data: pl.DataFrame | None = None,
) -> list[int]:
    """Resolve a public row selector to canonical final display rows."""

    def source_to_display(rows: list[int]) -> list[int]:
        return [layout.source_to_display(row) for row in rows]

    if i is None:
        return list(layout.data_rows)

    if isinstance(i, (list, tuple)) and i and any(isinstance(value, bool) for value in i):
        if not all(isinstance(value, bool) for value in i):
            raise TypeError("boolean row masks cannot mix booleans with other selector types")
        if data is None:
            raise TypeError("boolean row masks require source data")
        if len(i) != data.height:
            raise ValueError(
                f"boolean row mask has length {len(i)}, expected {data.height} source rows"
            )
        return source_to_display([j for j, value in enumerate(i) if value])

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

    if isinstance(i, (list, tuple)):
        rows: list[int] = []
        for value in i:
            if isinstance(value, str):
                rows.extend(layout.resolve_string(value))
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
    j: int | str | Sequence[int | str] | None,
    colnames: list[str],
    *,
    regex: bool = False,
) -> list[int]:
    """Resolve a public column selector to zero-based column indices."""
    if j is None:
        return list(range(len(colnames)))
    if isinstance(j, (list, tuple)):
        result: list[int] = []
        for value in j:
            resolved = _resolve_single_j(value, colnames, regex=regex)
            for idx in resolved:
                if idx not in result:
                    result.append(idx)
        return sorted(result)
    if isinstance(j, (int, str)):
        return _resolve_single_j(j, colnames, regex=regex)
    raise TypeError(f"bad column selector: {j!r}")


def _resolve_single_j(value: object, colnames: list[str], *, regex: bool) -> list[int]:
    if isinstance(value, bool):
        raise TypeError("column selector elements must be integers or strings, got bool")
    if isinstance(value, int):
        if value < 0 or value >= len(colnames):
            raise ValueError(
                f"column selector position {value} out of range for {len(colnames)} column(s)"
            )
        return [value]
    if isinstance(value, str):
        if regex:
            return _resolve_regex(value, colnames)
        if value in colnames:
            return [colnames.index(value)]
        raise ValueError(f"column not found: {value!r}")
    raise TypeError(
        f"column selector elements must be integers or strings, got {type(value).__name__}"
    )


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
