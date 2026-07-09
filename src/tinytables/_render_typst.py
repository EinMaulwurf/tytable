from __future__ import annotations

from dataclasses import dataclass

from ._colors import color_to_typst
from ._constants import STATIC_GET_STYLE_AND_SHOW_RULE
from ._escape import escape_typst
from ._indices import convert_row_to_typst
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

        if built.show_colnames:
            L.append("    table.header(")
            L.append("      repeat: true,")
            col_line = "      " + ",".join(f"[{c}]" for c in built.colnames_display) + ","
            L.append(col_line)
            L.append("    ),")

        for row in built.data_body:
            body_line = "    " + ",".join(f"[{cell}]" for cell in row) + ","
            L.append(body_line)

        L.append("  )")

        L.append("]")

        L.append(")")

        return "\n".join(L)

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
