"""The styling engine: selector resolution → batched style grid + line list.

Design rules (guide 06, 15): one batched pass over directives writing into a
single (i, j) -> props dict; overwrite non-line props (per-property
last-writer-wins), append line props. Never scan the grid per directive.
"""

from __future__ import annotations

import re

from ._indices import resolve_i, resolve_j

OVERWRITE_PROPS = (
    "bold", "italic", "underline", "strikeout", "monospace", "smallcaps",
    "align", "alignv", "color", "background", "fontsize", "indent",
    "colspan", "rowspan",
)

_ALIGN_H = {
    "l": "left", "left": "left",
    "c": "center", "center": "center",
    "r": "right", "right": "right",
}
_ALIGN_V = {
    "t": "top", "top": "top",
    "m": "horizon", "middle": "horizon",
    "b": "bottom", "bottom": "bottom",
}
_LINE_RE = re.compile(r"^[tblr]+$")


def align_to_typst(h, v) -> str | None:
    hs = _ALIGN_H.get(h) if h else None
    vs = _ALIGN_V.get(v) if v else None
    if hs and vs:
        return f"{hs} + {vs}"
    return hs or vs


def _validate_style(
    *, align, alignv, line, color, background, line_color,
    colspan, rowspan, line_width, fontsize, indent,
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
    for name, val in (("colspan", colspan), ("rowspan", rowspan)):
        if val is not None and (not isinstance(val, int) or isinstance(val, bool) or val < 1):
            raise ValueError(f"{name} must be a positive int, got {val!r}")
    if line_width is not None and (not isinstance(line_width, int | float) or isinstance(line_width, bool) or line_width < 0):
        raise ValueError(f"line_width must be a non-negative number, got {line_width!r}")
    for name, val in (("fontsize", fontsize), ("indent", indent)):
        if val is not None and (not isinstance(val, int | float) or isinstance(val, bool)):
            raise TypeError(f"{name} must be a number, got {type(val).__name__}")


def build_style_grid(table, *, nhead, has_header, n_merged_body, group_positions, output):
    """Resolve all style directives into one grid + a line list. guide 06 §3, 15 §2."""
    grid: dict[tuple[int, int], dict] = {}
    lines: list[dict] = []

    for d in table._style_directives:
        if d.output is not None and output not in d.output:
            continue
        i_vals = resolve_i(
            d.i, nhead=nhead, group_positions=group_positions,
            n_merged_body=n_merged_body, has_header=has_header,
        )
        if i_vals is None:
            i_vals = resolve_i(
                "all", nhead=nhead, group_positions=group_positions,
                n_merged_body=n_merged_body, has_header=has_header,
            )
        j_vals = resolve_j(d.j, table._colnames)
        has_line = d.line is not None

        for i in i_vals:
            for j in j_vals:
                cell = grid.setdefault((i, j), {})
                for prop in OVERWRITE_PROPS:
                    v = getattr(d, prop)
                    if v is not None:
                        cell[prop] = v
                if has_line:
                    lines.append({
                        "i": i, "j": j,
                        "line": d.line,
                        "line_color": d.line_color or "black",
                        "line_width": d.line_width if d.line_width is not None else 0.1,
                        "line_trim": d.line_trim,
                    })
    return grid, lines


def compute_covered_cells(style_grid):
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
