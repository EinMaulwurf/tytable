from __future__ import annotations

from dataclasses import dataclass

from ._colors import color_to_typst
from ._constants import STATIC_GET_STYLE_AND_SHOW_RULE
from ._escape import escape_typst
from ._indices import convert_col_to_typst, convert_row_to_typst
from ._styling import align_to_typst


def _props_to_signature(props):
    """Build the Typst style-array signature for one cell's props. guide 05 §3.1."""
    parts = []
    if props.get("bold"):
        parts.append("bold: true")
    if props.get("italic"):
        parts.append("italic: true")
    if props.get("underline"):
        parts.append("underline: true")
    if props.get("strikeout"):
        parts.append("strikeout: true")
    if props.get("monospace"):
        parts.append("mono: true")
    if props.get("smallcaps"):
        parts.append("smallcaps: true")
    if "color" in props:
        parts.append(f"color: {color_to_typst(props['color'])}")
    if "background" in props:
        parts.append(f"background: {color_to_typst(props['background'])}")
    if "fontsize" in props:
        parts.append(f"fontsize: {props['fontsize']}em")
    if "indent" in props and props["indent"] > 0:
        parts.append(f"indent: {props['indent']}em")
    align = align_to_typst(props.get("align"), props.get("alignv"))
    if align:
        parts.append(f"align: {align}")
    if not parts:
        return ""
    return ", ".join(parts) + ","


@dataclass
class TypstRenderOptions:
    figure: bool = True
    multipage: bool | None = None
    align_figure: str | None = None
    resize_width: float | None = None
    resize_direction: str | None = None
    grid_stroke: str | None = None
    rotate_angle: float | None = None
    portable: bool = False
    row_height_em: float | None = None


def _split_chunks(values):
    values = sorted(set(values))
    if not values:
        return []
    chunks = []
    start = prev = values[0]
    for v in values[1:]:
        if v != prev + 1:
            chunks.append((start, prev + 1))
            start = v
        prev = v
    chunks.append((start, prev + 1))
    return chunks


class TypstRenderer:
    def render(self, built, opts: TypstRenderOptions) -> str:
        L: list[str] = []

        if opts.multipage is not None:
            breakable = "true" if opts.multipage else "false"
            L.append(f"#show figure: set block(breakable: {breakable})")
        L.append("#figure(")
        if built.caption is not None:
            escaped = escape_typst(built.caption)
            L.append(f"  caption: text([{escaped}]),")
        L.append('  kind: "tinytable",')
        L.append('  supplement: "Table",')
        L.append("")

        L.append("block[")

        self._emit_style_block(L, built)
        L.append("")

        L.append("  #table(")

        ncol = len(built.colnames_display)
        cells = ["auto"] * ncol
        L.append(f"    columns: ({', '.join(cells)}),")

        if built.col_groups and not built.has_background:
            L.append("    column-gutter: 5pt,")

        L.append("    stroke: none,")

        if opts.row_height_em is not None:
            L.append(f"    rows: {opts.row_height_em}em,")
        else:
            L.append("    rows: auto,")

        L.append("    align: (x, y) => {")
        L.append("      let style = get-style(x, y)")
        L.append('      if style != none and "align" in style { style.align } else { left }')
        L.append("    },")

        L.append("    fill: (x, y) => {")
        L.append("      let style = get-style(x, y)")
        L.append('      if style != none and "background" in style { style.background }')
        L.append("    },")

        self._emit_lines(L, built)

        if built.show_colnames or built.col_groups:
            L.append("    table.header(")
            L.append("      repeat: true,")
            for row in built.col_groups:
                parts = self._build_col_group_row(row)
                L.append(f"      {', '.join(parts)},")
            if built.show_colnames:
                col_line = "      " + ",".join(f"[{c}]" for c in built.colnames_display) + ","
                L.append(col_line)
            L.append("    ),")

        covered = self._compute_covered_cells(built.style_grid)
        ncol = len(built.colnames_display)
        for r, row in enumerate(built.data_body):
            i_internal = r + 1
            parts = []
            for c, val in enumerate(row):
                j_internal = c + 1
                if (i_internal, j_internal) in covered:
                    continue
                span_props = built.style_grid.get((i_internal, j_internal), {})
                colspan = span_props.get("colspan", 1)
                rowspan = span_props.get("rowspan", 1)
                args = []
                if colspan > 1:
                    args.append(f"colspan: {colspan}")
                if rowspan > 1:
                    args.append(f"rowspan: {rowspan}")
                if args:
                    parts.append(f"table.cell({', '.join(args)})[{val}]")
                else:
                    parts.append(f"[{val}]")
            if parts:
                L.append("    " + ",".join(parts) + ",")

        L.append("  )")

        L.append("]")

        L.append(")")

        return "\n".join(L)

    def _emit_lines(self, L, built):
        hlines: dict[tuple[int, str], set[int]] = {}
        vlines: dict[tuple[int, str], set[int]] = {}

        for entry in built.style_lines:
            ti = convert_row_to_typst(entry["i"], built.nhead)
            tj = convert_col_to_typst(entry["j"])
            width = entry.get("line_width", 0.1)
            line_color = entry.get("line_color", "black")
            color_expr = color_to_typst(line_color)
            stroke = f"{width}em + {color_expr}"
            line = entry["line"]

            if "t" in line:
                hlines.setdefault((ti, stroke), set()).add(tj)
            if "b" in line:
                hlines.setdefault((ti + 1, stroke), set()).add(tj)
            if "l" in line:
                vlines.setdefault((tj, stroke), set()).add(ti)
            if "r" in line:
                vlines.setdefault((tj + 1, stroke), set()).add(ti)

        hline_entries = []
        for (y, stroke), cols in sorted(hlines.items()):
            for start, end in _split_chunks(cols):
                hline_entries.append((y, start, end, stroke))

        vline_entries = []
        for (x, stroke), rows in sorted(vlines.items()):
            for start, end in _split_chunks(rows):
                vline_entries.append((x, start, end, stroke))

        for y, start, end, stroke in sorted(hline_entries):
            L.append(
                f"    table.hline(y: {y}, start: {start}, end: {end}, stroke: {stroke}),"
            )

        for x, start, end, stroke in sorted(vline_entries):
            L.append(
                f"    table.vline(x: {x}, start: {start}, end: {end}, stroke: {stroke}),"
            )

    def _emit_style_block(self, L, built):
        styled = []
        for (i, j), props in built.style_grid.items():
            if not props:
                continue
            sig = _props_to_signature(props)
            if not sig:
                continue
            ti = convert_row_to_typst(i, built.nhead)
            tj = j - 1
            styled.append((ti, tj, sig))

        sig_to_idx: dict[str, int] = {}
        coord_entries: list[tuple[int, int, int]] = []
        for ti, tj, sig in styled:
            if sig not in sig_to_idx:
                sig_to_idx[sig] = len(sig_to_idx)
            coord_entries.append((ti, tj, sig_to_idx[sig]))

        L.append("  #let style-dict = (")
        for ti, tj, idx in coord_entries:
            L.append(f'    "{ti}_{tj}": {idx},')
        L.append("  )")
        L.append("")

        L.append("  #let style-array = (")
        idx_to_sig = {idx: sig for sig, idx in sig_to_idx.items()}
        for idx in range(len(idx_to_sig)):
            L.append(f"    ({idx_to_sig[idx]}),")
        L.append("  )")
        L.append("")

        L.append(STATIC_GET_STYLE_AND_SHOW_RULE)

    def _build_col_group_row(self, row):
        parts = []
        i = 0
        while i < len(row):
            v = row[i]
            if v is None:
                parts.append("[ ]")
                i += 1
                continue
            label = (v or "").strip()
            if label == "":
                parts.append("[ ]")
                i += 1
                continue
            start = i
            i += 1
            while i < len(row) and row[i] is not None and (row[i] or "").strip() == "":
                i += 1
            span = i - start
            escaped = escape_typst(label)
            if span > 1:
                parts.append(f"table.cell(colspan: {span}, align: center)[{escaped}]")
            else:
                parts.append(f"[{escaped}]")
        return parts

    def _compute_covered_cells(self, style_grid):
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
