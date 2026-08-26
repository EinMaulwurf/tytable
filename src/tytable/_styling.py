"""
The styling engine: selector resolution → batched style grid + line list.

Style directives are resolved in one batched pass into a single
``(i, j) -> props`` mapping. Cell properties use per-property
last-writer-wins semantics. Border instructions remain ordered until renderers
resolve them into last-writer-wins physical grid edges. The pass never scans
the grid per directive.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from ._colors import _is_color_function, _validate_color_string
from ._groups import _resolve_col_group_spans
from ._indices import resolve_i, resolve_where

if TYPE_CHECKING:
    from ._directives import StyleDirective
    from ._indices import RowLayout
    from ._tytable import TyTable

OVERWRITE_PROPS = (
    "bold",
    "italic",
    "underline",
    "strikeout",
    "monospace",
    "smallcaps",
    "align",
    "alignv",
    "color",
    "background",
    "fontsize",
    "indent",
    "padding",
    "colspan",
    "rowspan",
    "rotate",
)

# Props applicable to the non-grid "caption" / "notes" meta selectors
# (everything in OVERWRITE_PROPS except the grid-only span controls).
META_STYLE_PROPS = tuple(p for p in OVERWRITE_PROPS if p not in ("padding", "colspan", "rowspan"))

_META_STYLE_SUPPORT = {
    "typst": {
        "caption": {
            "bold",
            "italic",
            "underline",
            "strikeout",
            "smallcaps",
            "color",
            "fontsize",
        },
        "notes": {
            "bold",
            "italic",
            "underline",
            "strikeout",
            "smallcaps",
            "color",
            "background",
            "fontsize",
            "align",
            "alignv",
            "indent",
        },
    },
    "html": {
        "caption": {
            "bold",
            "italic",
            "underline",
            "strikeout",
            "monospace",
            "smallcaps",
            "color",
            "background",
            "fontsize",
            "align",
            "indent",
        },
        "notes": {
            "bold",
            "italic",
            "underline",
            "strikeout",
            "monospace",
            "smallcaps",
            "color",
            "background",
            "fontsize",
            "align",
            "alignv",
            "indent",
        },
    },
}

# Selectors handled outside the row/column style grid (see ``build_meta_styles``).
META_SELECTORS = ("caption", "notes")

_ALIGN_H = {
    "l": "left",
    "left": "left",
    "c": "center",
    "center": "center",
    "r": "right",
    "right": "right",
}
_ALIGN_V = {
    "t": "top",
    "top": "top",
    "m": "horizon",
    "middle": "horizon",
    "b": "bottom",
    "bottom": "bottom",
}
_LINE_RE = re.compile(r"^[tblr]+$")
_LINE_STYLES = {"solid", "dashed", "dotted", "dash-dotted", "none"}

StyleValidator = Callable[[str, object], None]
Padding: TypeAlias = float | tuple[float, float] | tuple[float, float, float, float]


def align_to_typst(h: str | None, v: str | None) -> str | None:
    """Translate horizontal/vertical alignment shorthands into a Typst ``align`` expression."""
    hs = _ALIGN_H.get(h) if h else None
    vs = _ALIGN_V.get(v) if v else None
    if hs and vs:
        return f"{hs} + {vs}"
    return hs or vs


def _expand_align(
    val: str | None, n_cols: int, table: dict[str, str], name: str
) -> list[str] | None:
    """Expand an align/alignv value into per-column shorthand values.

    A single value (e.g. ``"l"``, ``"left"``) is broadcast to all columns.
    A multi-char shorthand string (e.g. ``"llr"``) is split per-column,
    one character per selected column.
    """
    if val is None:
        return None
    if val in table:
        return [val] * n_cols
    if len(val) != n_cols:
        raise ValueError(
            f"{name} spec {val!r} has {len(val)} chars but {n_cols} column(s) were selected"
        )
    return list(val)


def _validate_align(name: str, value: object) -> None:
    """Validate horizontal or vertical alignment syntax."""
    if value is None:
        return
    table = _ALIGN_H if name == "align" else _ALIGN_V
    if not isinstance(value, str) or (value not in table and not all(c in table for c in value)):
        raise ValueError(f"invalid {name} value: {value!r}")


def _validate_line(name: str, value: object) -> None:
    """Validate a cell-edge line specification."""
    if value is not None and (not isinstance(value, str) or not _LINE_RE.match(value)):
        raise ValueError(f"invalid {name} value: {value!r} (must be a combo of t,b,l,r)")


def _validate_line_style(name: str, value: object) -> None:
    """Validate a portable cell-edge stroke style."""
    if value is not None and (not isinstance(value, str) or value not in _LINE_STYLES):
        choices = ", ".join(sorted(_LINE_STYLES))
        raise ValueError(f"invalid {name} value: {value!r} (expected one of {choices})")


def _validate_color(name: str, value: object) -> None:
    """Validate a color-valued style property."""
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    try:
        _validate_color_string(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {exc}") from exc


def _validate_positive_int(name: str, value: object) -> None:
    """Validate a positive integer span property."""
    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
        raise ValueError(f"{name} must be a positive int, got {value!r}")


def _validate_non_negative_number(name: str, value: object) -> None:
    """Validate a non-negative numeric style property."""
    if value is not None and (not isinstance(value, int | float) or isinstance(value, bool)):
        raise ValueError(f"{name} must be a non-negative number, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if isinstance(value, int | float) and value < 0:
        raise ValueError(f"{name} must be a non-negative number, got {value!r}")


def _validate_number(name: str, value: object) -> None:
    """Validate a numeric style property."""
    if value is not None and (not isinstance(value, int | float) or isinstance(value, bool)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")


def _validate_non_negative_style_number(name: str, value: object) -> None:
    """Validate a numeric style property whose unit cannot be negative."""
    _validate_number(name, value)
    if isinstance(value, int | float) and value < 0:
        raise ValueError(f"{name} must be non-negative, got {value!r}")


def normalize_padding(value: float | Sequence[float] | None) -> Padding | None:
    """Validate and normalize a public cell-padding specification."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("padding must be a number or a sequence of two or four numbers")
    if isinstance(value, int | float):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"padding values must be finite, got {value!r}")
        if value < 0:
            raise ValueError(f"padding values must be non-negative, got {value!r}")
        return value
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError("padding must be a number or a sequence of two or four numbers")
    values = tuple(value)
    if len(values) not in (2, 4):
        raise ValueError(f"padding must contain two or four values, got {len(values)}")
    for item in values:
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise TypeError(f"padding values must be numbers, got {item!r}")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError(f"padding values must be finite, got {item!r}")
        if item < 0:
            raise ValueError(f"padding values must be non-negative, got {item!r}")
    if len(values) == 2:
        return values[0], values[1]
    return values[0], values[1], values[2], values[3]


_STYLE_VALIDATORS: dict[str, StyleValidator] = {
    "align": _validate_align,
    "alignv": _validate_align,
    "line": _validate_line,
    "line_style": _validate_line_style,
    "color": _validate_color,
    "background": _validate_color,
    "line_color": _validate_color,
    "colspan": _validate_positive_int,
    "rowspan": _validate_positive_int,
    "line_width": _validate_non_negative_number,
    "fontsize": _validate_non_negative_style_number,
    "indent": _validate_non_negative_style_number,
    "rotate": _validate_number,
}


def _validate_style(
    *,
    align: str | None,
    alignv: str | None,
    line: str | None,
    line_style: str | None,
    color: str | None,
    background: str | None,
    line_color: str | None,
    colspan: int | None,
    rowspan: int | None,
    line_width: int | float | None,
    fontsize: int | float | None,
    indent: int | float | None,
    rotate: int | float | None,
    output: tuple[str, ...] | None,
) -> None:
    """Fail fast on invalid style values when ``.style()`` is called."""
    values = locals()
    for name, validator in _STYLE_VALIDATORS.items():
        validator(name, values[name])
    if output is None or "html" in output:
        for name in ("color", "background", "line_color"):
            value = values[name]
            if value is not None and _is_color_function(value):
                raise ValueError(
                    f"{name}={value!r} is a Typst color expression; restrict the style "
                    'directive with output=("typst",)'
                )


def build_style_grid(
    table: TyTable,
    *,
    layout: RowLayout,
    output: str,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    """Resolve all style directives into one grid and an ordered line list."""
    # Row-group labels are descriptive text, even when they span from a
    # numeric first column. User directives below retain last-writer priority.
    grid: dict[tuple[int, int], dict] = {(i, 0): {"align": "l"} for i in layout.groupi_rows}
    lines: list[dict] = []
    from ._themes import apply_base_theme

    apply_base_theme(table, layout, table._data.width, grid, lines)
    groupj_cells = _groupj_cell_map(table, layout)

    for d in table._style_directives:
        if d.output is not None and output not in d.output:
            continue
        if isinstance(d.i, str) and d.i in META_SELECTORS:
            # Caption/notes styling is resolved separately in ``build_meta_styles``;
            # they are not grid cells, so skip them here.
            continue
        i_vals = resolve_i(
            d.i,
            layout=layout,
            data=table._data,
        )
        j_vals = table._resolve_j(d.j)
        where_cells = (
            resolve_where(d.where, data=table._data, layout=layout) if d.where is not None else None
        )
        has_line = d.line is not None
        active_props = {
            prop: value for prop in OVERWRITE_PROPS if (value := getattr(d, prop)) is not None
        }
        align_vals = _expand_align(d.align, len(j_vals), _ALIGN_H, "align")
        alignv_vals = _expand_align(d.alignv, len(j_vals), _ALIGN_V, "alignv")

        for i in i_vals:
            resolved_cells: dict[int, tuple[tuple[int, ...], str | None, str | None]] = {}
            for idx, j in enumerate(j_vals):
                if where_cells is not None and (i, j) not in where_cells:
                    continue
                target_j = j
                members: tuple[int, ...] = (j,)
                if layout.kind(i) == "groupj":
                    group_cell = groupj_cells.get((i, j))
                    if group_cell is None:
                        continue
                    target_j, members = group_cell
                align = align_vals[idx] if align_vals is not None else None
                alignv = alignv_vals[idx] if alignv_vals is not None else None
                previous = resolved_cells.get(target_j)
                if previous is not None:
                    _, previous_align, previous_alignv = previous
                    if previous_align != align or previous_alignv != alignv:
                        raise ValueError(
                            "per-column alignment assigns conflicting values to one "
                            "column-group header cell"
                        )
                    continue
                resolved_cells[target_j] = (members, align, alignv)

            for target_j, (members, align, alignv) in resolved_cells.items():
                cell = grid.setdefault((i, target_j), {})
                # A cell can have only one final value for properties such as
                # color. Borders remain ordered commands until each renderer
                # resolves neighboring cell sides onto physical grid edges.
                cell.update(active_props)
                if align is not None:
                    cell["align"] = align
                if alignv is not None:
                    cell["alignv"] = alignv
                if has_line:
                    _append_cell_lines(lines, d, i=i, members=members)
    return grid, lines


def _groupj_cell_map(
    table: TyTable, layout: RowLayout
) -> dict[tuple[int, int], tuple[int, tuple[int, ...]]]:
    """Map visible source columns to their spanning header cell and visible members."""
    visible = set(table._display_columns)
    result: dict[tuple[int, int], tuple[int, tuple[int, ...]]] = {}
    for display_row in layout.groupj_rows:
        level = layout.groupj_level(display_row)
        source_row = table._col_group_rows[-level - 1]
        for _label, start, span in _resolve_col_group_spans(source_row):
            members = tuple(col for col in range(start, start + span) if col in visible)
            if not members:
                continue
            target = members[0]
            for col in members:
                result[(display_row, col)] = (target, members)
    return result


def _append_cell_lines(
    lines: list[dict[str, Any]], directive: StyleDirective, *, i: int, members: tuple[int, ...]
) -> None:
    """Append borders for one resolved cell, expanding horizontal span edges."""
    if directive.line is None:
        return
    sides_by_column: dict[int, list[str]] = {}
    for side in directive.line:
        if side in "tb":
            targets = members
        elif side == "l":
            targets = members[:1]
        else:
            targets = members[-1:]
        for column in targets:
            sides = sides_by_column.setdefault(column, [])
            if side not in sides:
                sides.append(side)
    for column, sides in sides_by_column.items():
        lines.append(
            {
                "i": i,
                "j": column,
                "line": "".join(sides),
                "line_style": directive.line_style or "solid",
                "line_color": directive.line_color or "black",
                "line_width": directive.line_width if directive.line_width is not None else 0.1,
            }
        )


def build_meta_styles(
    table: TyTable,
    *,
    output: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve ``i="caption"`` / ``i="notes"`` style directives into two prop dicts.

    Caption and footnotes are not grid cells, so they bypass the
    ``(row, col) -> props`` style grid: directives targeting the ``"caption"``
    or ``"notes"`` selectors are collected here (last-writer-wins per property)
    and the renderers apply them by wrapping the caption/notes text with the
    backend's inline styling markup.
    """
    style_caption: dict[str, Any] = {}
    style_notes: dict[str, Any] = {}
    for d in table._style_directives:
        if d.output is not None and output not in d.output:
            continue
        if not isinstance(d.i, str):
            continue
        if d.i == "caption":
            target = style_caption
        elif d.i == "notes":
            target = style_notes
        else:
            continue
        if d.where is not None:
            raise ValueError(f"where cannot be used with the {d.i!r} selector")
        if d.j is not None:
            raise ValueError(f"j cannot be used with the {d.i!r} selector")
        if d.line is not None or d.line_style is not None or d.line_color is not None:
            raise ValueError(f"line styling cannot be used with the {d.i!r} selector")
        if d.colspan is not None or d.rowspan is not None:
            raise ValueError(f"spans cannot be used with the {d.i!r} selector")
        supported = _META_STYLE_SUPPORT.get(output, {}).get(d.i)
        for prop in META_STYLE_PROPS:
            v = getattr(d, prop)
            if v is not None:
                if prop == "align" and isinstance(v, str) and v not in _ALIGN_H:
                    raise ValueError(
                        f"per-column align spec {v!r} cannot be used with meta selector {d.i!r}"
                    )
                if prop == "alignv" and isinstance(v, str) and v not in _ALIGN_V:
                    raise ValueError(
                        f"per-column alignv spec {v!r} cannot be used with meta selector {d.i!r}"
                    )
                if supported is not None and prop not in supported:
                    raise ValueError(
                        f"style property {prop!r} is not supported for {d.i!r} in {output} output"
                    )
                target[prop] = v
    return style_caption, style_notes


def compute_covered_cells(
    style_grid: dict[tuple[int, int], dict[str, Any]],
) -> set[tuple[int, int]]:
    """Return the set of (row, col) cells hidden by a spanning cell."""
    covered = set()
    for (r, c), props in style_grid.items():
        scol = props.get("colspan")
        srow = props.get("rowspan")
        if not isinstance(scol, int):
            scol = 1
        if not isinstance(srow, int):
            srow = 1
        if scol > 1 or srow > 1:
            for rr in range(r, r + srow):
                for cc in range(c, c + scol):
                    if rr == r and cc == c:
                        continue
                    covered.add((rr, cc))
    return covered


def resolve_line_edges(
    style_lines: list[dict[str, Any]],
) -> dict[tuple[str, int, int], dict[str, Any]]:
    """Resolve ordered cell-side commands into last-writer-wins physical grid edges.

    Keys are ``(axis, boundary, segment)``. For a horizontal edge, ``boundary``
    is its y coordinate and ``segment`` its column; for a vertical edge they
    are its x coordinate and row. The retained value also records which cell
    side supplied the winning command so HTML can place the collapsed border.
    """
    edges: dict[tuple[str, int, int], dict[str, Any]] = {}
    for entry in style_lines:
        i = entry["i"]
        j = entry["j"]
        for side in entry["line"]:
            if side == "t":
                key = ("h", i, j)
            elif side == "b":
                key = ("h", i + 1, j)
            elif side == "l":
                key = ("v", j, i)
            else:
                key = ("v", j + 1, i)
            edges[key] = {**entry, "cell_i": i, "cell_j": j, "side": side}
    return edges
