"""
The styling engine: selector resolution → batched style grid + line list.

Design rules (guide 06, 15): one batched pass over directives writing into a
single (i, j) -> props dict; overwrite non-line props (per-property
last-writer-wins), append line props. Never scan the grid per directive.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ._indices import resolve_i, resolve_j

if TYPE_CHECKING:
    from ._tytable import TinyTable

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
)

# Props applicable to the non-grid "caption" / "notes" meta selectors
# (everything in OVERWRITE_PROPS except the grid-only span controls).
META_STYLE_PROPS = tuple(p for p in OVERWRITE_PROPS if p not in ("colspan", "rowspan"))

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


def align_to_typst(h: str | None, v: str | None) -> str | None:
    """Translate horizontal/vertical alignment shorthands into a Typst ``align`` expression."""
    hs = _ALIGN_H.get(h) if h else None
    vs = _ALIGN_V.get(v) if v else None
    if hs and vs:
        return f"{hs} + {vs}"
    return hs or vs


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
) -> None:
    """Fail-fast validation at .style() call time. guide 06 §7."""
    for name, val in (("align", align), ("alignv", alignv)):
        if val is not None:
            table = _ALIGN_H if name == "align" else _ALIGN_V
            if val not in table:
                raise ValueError(f"invalid {name} value: {val!r}")
    if line is not None and not _LINE_RE.match(line):
        raise ValueError(f"invalid line value: {line!r} (must be a combo of t,b,l,r)")
    for name, val in (("color", color), ("background", background), ("line_color", line_color)):
        if val is not None and not isinstance(val, str):
            raise TypeError(f"{name} must be a string, got {type(val).__name__}")
    for name, ival in (("colspan", colspan), ("rowspan", rowspan)):
        if ival is not None and (not isinstance(ival, int) or isinstance(ival, bool) or ival < 1):
            raise ValueError(f"{name} must be a positive int, got {ival!r}")
    if line_width is not None and (
        not isinstance(line_width, int | float) or isinstance(line_width, bool) or line_width < 0
    ):
        raise ValueError(f"line_width must be a non-negative number, got {line_width!r}")
    for name, nval in (("fontsize", fontsize), ("indent", indent)):
        if nval is not None and (not isinstance(nval, int | float) or isinstance(nval, bool)):
            raise TypeError(f"{name} must be a number, got {type(nval).__name__}")


def build_style_grid(
    table: TinyTable,
    *,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
    output: str,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    """Resolve all style directives into one grid + a line list. guide 06 §3, 15 §2."""
    grid: dict[tuple[int, int], dict] = {}
    lines: list[dict] = []

    for d in table._style_directives:
        if d.output is not None and output not in d.output:
            continue
        if d.i in META_SELECTORS:
            # Caption/notes styling is resolved separately in ``build_meta_styles``;
            # they are not grid cells, so skip them here.
            continue
        i_vals = resolve_i(
            d.i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
        )
        if i_vals is None:
            i_vals = resolve_i(
                "all",
                nhead=nhead,
                group_positions=group_positions,
                n_merged_body=n_merged_body,
                has_header=has_header,
            )
        j_vals = resolve_j(d.j, table._colnames)
        has_line = d.line is not None
        if i_vals is None:
            continue

        for i in i_vals:
            for j in j_vals:
                cell = grid.setdefault((i, j), {})
                for prop in OVERWRITE_PROPS:
                    v = getattr(d, prop)
                    if v is not None:
                        cell[prop] = v
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
    table: TinyTable,
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
        if d.i == "caption":
            target = style_caption
        elif d.i == "notes":
            target = style_notes
        else:
            continue
        for prop in META_STYLE_PROPS:
            v = getattr(d, prop)
            if v is not None:
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
