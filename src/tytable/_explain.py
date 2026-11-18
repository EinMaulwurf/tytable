"""Describe directive selections without running the render pipeline."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from tytable._directives import FormatDirective, ImageDirective, Note, PlotDirective, StyleDirective
from tytable._groups import row_group_positions
from tytable._indices import RowKind, RowLayout, resolve_i, resolve_where
from tytable._resolve import resolve_layout, validate_output
from tytable._styling import _groupj_cell_map, _split_meta_selectors

if TYPE_CHECKING:
    from tytable._renderer import OutputFormat
    from tytable._tytable import TyTable

_Directive = FormatDirective | ImageDirective | Note | PlotDirective | StyleDirective
_METHODS = {
    FormatDirective: ".fmt()",
    ImageDirective: ".images()",
    Note: "notes",
    PlotDirective: ".plot()",
    StyleDirective: ".style()",
}


def explain(table: TyTable, output: OutputFormat) -> str:
    """Use the render layout and selectors to report each directive's targets."""
    validate_output(output)
    layout, _ = resolve_layout(table, row_group_positions(table._row_groups))
    groupj_cells = _groupj_cell_map(table, layout)
    lines = [f"TyTable directives for {output!r}"]

    directives = (
        table._format_directives,
        table._media_directives,
        table._notes,
        table._style_directives,
    )
    for collection in directives:
        for number, directive in enumerate(collection, start=1):
            method = _METHODS[type(directive)]
            prefix = f"{method} #{number}"
            if not isinstance(directive, Note):
                outputs = directive.output
                if outputs is not None and output not in outputs:
                    lines.append(f"{prefix}  skipped (output={outputs!r})")
                    continue
            details, count = _describe_selection(table, layout, groupj_cells, directive, method)
            empty = " (empty selection)" if count == 0 else ""
            lines.append(f"{prefix}  {details}  targets={count}{empty}")

    if len(lines) == 1:
        lines.append("No directives recorded")
    return "\n".join(lines)


def _describe_selection(
    table: TyTable,
    layout: RowLayout,
    groupj_cells: dict[tuple[int, int], tuple[int, tuple[int, ...]]],
    directive: _Directive,
    method: str,
) -> tuple[str, int]:
    i, j = directive.i, directive.j
    where = (
        directive.where if isinstance(directive, FormatDirective | Note | StyleDirective) else None
    )
    if isinstance(directive, Note) and i is None and j is None and where is None:
        return "table note", 1

    meta: tuple[str, ...] = ()
    if isinstance(directive, StyleDirective):
        i, meta = _split_meta_selectors(directive.i)
    rows = resolve_i(i, layout=layout, data=table._data)
    if not isinstance(directive, StyleDirective):
        allowed: set[RowKind] = {"groupi", "data"}
        if isinstance(directive, FormatDirective | Note):
            allowed.add("header")
        layout.require_supported(rows, allowed=allowed, method=method)

    cols = table._resolve_j(j)
    names = table._source_colnames
    details = f"rows={rows!r} columns={[names[col] for col in cols]!r}"

    if where is None:
        group_rows = [row for row in rows if row < layout.column_group_rows]
        count = (len(rows) - len(group_rows)) * len(cols)
        for row in group_rows:
            count += len({groupj_cells[row, col][0] for col in cols if (row, col) in groupj_cells})
    else:
        selected_rows, selected_cols = set(rows), set(cols)
        matches: dict[str, list[int]] = defaultdict(list)
        for row, col in sorted(resolve_where(where, data=table._data, layout=layout)):
            if row in selected_rows and col in selected_cols:
                matches[names[col]].append(row)
        details += f" where={dict(matches)!r}"
        count = sum(map(len, matches.values()))

    if meta:
        metadata_counts = {"caption": int(table._caption is not None), "notes": len(table._notes)}
        details += f" metadata={list(meta)!r}"
        count += sum(metadata_counts[target] for target in meta)
    return details, count
