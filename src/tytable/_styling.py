"""
The styling engine: selector resolution → batched style grid + line list.

Style directives are resolved in one batched pass into a single
``(i, j) -> props`` mapping. Cell properties use per-property
last-writer-wins semantics, while border instructions remain ordered so that
multiple edges and strokes can coexist. The pass never scans the grid per
directive.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ._colors import _is_color_function, _validate_color_string
from ._indices import resolve_i, resolve_j, resolve_where

if TYPE_CHECKING:
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
    "colspan",
    "rowspan",
    "rotate",
)

# Props applicable to the non-grid "caption" / "notes" meta selectors
# (everything in OVERWRITE_PROPS except the grid-only span controls).
META_STYLE_PROPS = tuple(p for p in OVERWRITE_PROPS if p not in ("colspan", "rowspan"))

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

StyleValidator = Callable[[str, object], None]


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
    if value is not None and (
        not isinstance(value, int | float) or isinstance(value, bool) or value < 0
    ):
        raise ValueError(f"{name} must be a non-negative number, got {value!r}")


def _validate_number(name: str, value: object) -> None:
    """Validate a numeric style property."""
    if value is not None and (not isinstance(value, int | float) or isinstance(value, bool)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")


_STYLE_VALIDATORS: dict[str, StyleValidator] = {
    "align": _validate_align,
    "alignv": _validate_align,
    "line": _validate_line,
    "color": _validate_color,
    "background": _validate_color,
    "line_color": _validate_color,
    "colspan": _validate_positive_int,
    "rowspan": _validate_positive_int,
    "line_width": _validate_non_negative_number,
    "fontsize": _validate_number,
    "indent": _validate_number,
    "rotate": _validate_number,
}


def _validate_style(
    *,
    align: str | None,
    alignv: str | None,
    line: str | None,
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
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
    output: str,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    """Resolve all style directives into one grid and an ordered line list."""
    # Row-group labels are descriptive text, even when they span from a
    # numeric first column. User directives below retain last-writer priority.
    grid: dict[tuple[int, int], dict] = {(i, 1): {"align": "l"} for i in group_positions}
    lines: list[dict] = []

    for d in table._style_directives:
        if d.output is not None and output not in d.output:
            continue
        if isinstance(d.i, str) and d.i in META_SELECTORS:
            # Caption/notes styling is resolved separately in ``build_meta_styles``;
            # they are not grid cells, so skip them here.
            continue
        i_vals = resolve_i(
            d.i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
            data=table._data,
        )
        if i_vals is None:
            i_vals = resolve_i(
                "all",
                nhead=nhead,
                group_positions=group_positions,
                n_merged_body=n_merged_body,
                has_header=has_header,
            )
        j_vals = resolve_j(d.j, table._colnames, regex=d.regex)
        where_cells = (
            resolve_where(d.where, data=table._data, group_positions=group_positions)
            if d.where is not None
            else None
        )
        has_line = d.line is not None
        if i_vals is None:
            continue

        active_props = {
            prop: value for prop in OVERWRITE_PROPS if (value := getattr(d, prop)) is not None
        }
        align_vals = _expand_align(d.align, len(j_vals), _ALIGN_H, "align")
        alignv_vals = _expand_align(d.alignv, len(j_vals), _ALIGN_V, "alignv")

        for i in i_vals:
            for idx, j in enumerate(j_vals):
                if where_cells is not None and (i, j) not in where_cells:
                    continue
                cell = grid.setdefault((i, j), {})
                # A cell can have only one final value for properties such as
                # color, but borders are drawing commands: retaining every
                # matching line directive allows independent/overlaid edges.
                cell.update(active_props)
                if align_vals is not None:
                    cell["align"] = align_vals[idx]
                if alignv_vals is not None:
                    cell["alignv"] = alignv_vals[idx]
                if has_line:
                    lines.append(
                        {
                            "i": i,
                            "j": j,
                            "line": d.line,
                            "line_color": d.line_color or "black",
                            "line_width": d.line_width if d.line_width is not None else 0.1,
                            "line_trim": d.line_trim,
                        }
                    )
    return grid, lines


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
        if d.regex:
            raise ValueError(f"regex cannot be used with the {d.i!r} selector")
        if d.line is not None or d.line_color is not None or d.line_trim is not None:
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
