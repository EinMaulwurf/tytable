from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._colors import color_to_typst
from ._constants import STATIC_GET_STYLE_AND_SHOW_RULE
from ._escape import escape_typst
from ._indices import convert_col_to_typst, convert_row_to_typst
from ._resolve import BuiltTable
from ._styling import align_to_typst, compute_covered_cells


def _props_to_signature(props: dict[str, Any]) -> str:
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
    column_gutter: float | str | None = 2

    def align_to_typst(self) -> str:
        return {"l": "left", "c": "center", "r": "right"}.get(self.align_figure or "l", "left")


def _split_chunks(values: set[int]) -> list[tuple[int, int]]:
    sorted_values = sorted(values)
    if not sorted_values:
        return []
    chunks = []
    start = prev = sorted_values[0]
    for v in sorted_values[1:]:
        if v != prev + 1:
            chunks.append((start, prev + 1))
            start = v
        prev = v
    chunks.append((start, prev + 1))
    return chunks


class TypstRenderer:
    @staticmethod
    def _columns_spec(width: float | str | list[float | str | None] | None, ncol: int) -> list[str]:
        if width is None:
            return ["auto"] * ncol
        if isinstance(width, str):
            return [width] * ncol
        if isinstance(width, (int, float)):
            return [f"{width / ncol * 100:.2f}%"] * ncol
        result = []
        for w in width:
            if w is None:
                result.append("auto")
            elif isinstance(w, str):
                result.append(w)
            else:
                result.append(f"{w * 100:.2f}%")
        return result

    def render(self, built: BuiltTable, opts: TypstRenderOptions) -> str:
        L: list[str] = []
        need_figure = opts.figure

        if need_figure and opts.multipage is not None:
            breakable = "true" if opts.multipage else "false"
            L.append(f"#show figure: set block(breakable: {breakable})")
        elif not need_figure and opts.multipage is not None:
            breakable = "true" if opts.multipage else "false"
            L.append(f"#set page(breakable: {breakable})")

        if need_figure:
            L.append("#figure(")
            if built.caption is not None:
                escaped = escape_typst(built.caption)
                L.append(f"  caption: text([{escaped}]),")
            L.append('  kind: "tytable",')
            L.append('  supplement: "Table",')
            L.append("")
            L.append("block[")
        else:
            L.append("#table(")

        if need_figure:
            self._emit_style_block(L, built)
            L.append("")

        ncol = len(built.colnames_display)

        if need_figure:
            L.append("  #table(")

        cells = self._columns_spec(built.width, ncol)
        L.append(f"    columns: ({', '.join(cells)}),")

        if built.col_groups and not built.has_background:
            gutter = opts.column_gutter
            if gutter is not None:
                unit = "pt" if isinstance(gutter, (int, float)) else ""
                L.append(f"    column-gutter: {gutter}{unit},")

        stroke_val = opts.grid_stroke if opts.grid_stroke else "none"
        L.append(f"    stroke: {stroke_val},")

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

        covered = compute_covered_cells(built.style_grid)
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

        self._emit_footer(L, built, ncol)

        L.append("  )")

        if need_figure:
            L.append("]")
            L.append(")")

        if opts.align_figure:
            aligned = opts.align_to_typst()
            L = [
                f"#align({aligned}, [",
                *L,
                "])",
            ]
        if opts.rotate_angle is not None:
            L = [
                f"#rotate({opts.rotate_angle}deg, reflow: true, [",
                *L,
                "])",
            ]

        return "\n".join(L)

    def _emit_footer(self, L: list[str], built: BuiltTable, ncol: int) -> None:
        notes = built.notes
        if not notes:
            return

        L.append("    table.footer(")
        L.append("      repeat: false,")
        for note in notes:
            escaped = escape_typst(note.text)
            if note.marker:
                L.append(
                    f"      table.cell(align: left, colspan: {ncol},"
                    f" [#super[{escape_typst(note.marker)}] {escaped}]),"
                )
            else:
                L.append(f"      table.cell(align: left, colspan: {ncol}, [{escaped}]),")
        L.append("    ),")

    def _emit_lines(self, L: list[str], built: BuiltTable) -> None:
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
            L.append(f"    table.hline(y: {y}, start: {start}, end: {end}, stroke: {stroke}),")

        for x, start, end, stroke in sorted(vline_entries):
            L.append(f"    table.vline(x: {x}, start: {start}, end: {end}, stroke: {stroke}),")

    def _emit_style_block(self, L: list[str], built: BuiltTable) -> None:
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

    def _build_col_group_row(self, row: list[str | None]) -> list[str]:
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
