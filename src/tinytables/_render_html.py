from __future__ import annotations

from ._escape import escape_html


def _align_to_css(h, v) -> str | None:
    if v == "m":
        v = "middle"
    if v == "horizon":
        v = "middle"
    parts = []
    if h:
        parts.append({"l": "left", "c": "center", "r": "right"}.get(h, h))
    if v:
        parts.append({"t": "top", "b": "bottom"}.get(v, v))
    return " ".join(parts) if parts else None


def _build_cell_style(cell_props, border_css):
    css_parts: list[str] = []

    if border_css:
        css_parts.append(border_css)

    if cell_props.get("bold"):
        css_parts.append("font-weight:bold")
    if cell_props.get("italic"):
        css_parts.append("font-style:italic")
    if cell_props.get("underline"):
        css_parts.append("text-decoration:underline")
    if cell_props.get("strikeout"):
        css_parts.append("text-decoration:line-through")
    if cell_props.get("monospace"):
        css_parts.append("font-family:monospace")
    if cell_props.get("smallcaps"):
        css_parts.append("font-variant:small-caps")
    if "color" in cell_props:
        css_parts.append(f"color:{cell_props['color']}")
    if "background" in cell_props:
        css_parts.append(f"background-color:{cell_props['background']}")
    if "fontsize" in cell_props:
        css_parts.append(f"font-size:{cell_props['fontsize']}em")
    if "indent" in cell_props and cell_props["indent"] > 0:
        css_parts.append(f"padding-left:{cell_props['indent']}em")

    align = _align_to_css(
        cell_props.get("align"),
        cell_props.get("alignv"),
    )
    if align:
        css_parts.append(f"text-align:{align}")

    return "; ".join(css_parts) if css_parts else ""


def _build_border_map(style_lines, nhead):
    from ._indices import convert_col_to_typst, convert_row_to_typst

    border_map: dict[tuple[int, int], str] = {}
    for entry in style_lines:
        ti = convert_row_to_typst(entry["i"], nhead)
        tj = convert_col_to_typst(entry["j"])
        width = entry.get("line_width", 0.1)
        line_color = entry.get("line_color", "black")
        line = entry["line"]

        borders = border_map.setdefault((ti, tj), "")
        for side in line:
            if side == "t":
                borders += f"border-top:{width}em solid {line_color};"
            elif side == "b":
                borders += f"border-bottom:{width}em solid {line_color};"
            elif side == "l":
                borders += f"border-left:{width}em solid {line_color};"
            elif side == "r":
                borders += f"border-right:{width}em solid {line_color};"
        border_map[(ti, tj)] = borders
    return border_map


class HtmlRenderer:
    def render(self, built, _opts=None) -> str:
        ncol = len(built.colnames_display)
        border_map = _build_border_map(built.style_lines, built.nhead)

        parts: list[str] = []
        table_style = "border-collapse:collapse;font-family:sans-serif;font-size:1em"
        if built.width is not None and isinstance(built.width, (int, float)):
                table_style += f";width:{built.width}%"
        parts.append(f'<table style="{table_style}">')

        if built.caption is not None:
            escaped = escape_html(built.caption)
            parts.append(f"<caption>{escaped}</caption>")

        head_parts: list[str] = []
        if built.col_groups:
            for row in built.col_groups:
                tr_parts: list[str] = []
                i_col = 0
                while i_col < len(row):
                    v = row[i_col]
                    if v is None:
                        tr_parts.append("<th></th>")
                        i_col += 1
                        continue
                    label = (v or "").strip()
                    if label == "":
                        tr_parts.append("<th></th>")
                        i_col += 1
                        continue
                    start = i_col
                    i_col += 1
                    while i_col < len(row) and row[i_col] is not None and (row[i_col] or "").strip() == "":
                        i_col += 1
                    span = i_col - start
                    escaped_label = escape_html(label)
                    if span > 1:
                        tr_parts.append(
                            f'<th colspan="{span}" style="text-align:center">{escaped_label}</th>'
                        )
                    else:
                        tr_parts.append(f'<th style="text-align:center">{escaped_label}</th>')
                head_parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        if built.show_colnames:
            tr_parts: list[str] = []
            for j, c in enumerate(built.colnames_display):
                style_str = ""
                i_internal = 0
                j_internal = j + 1
                cell_props = built.style_grid.get((i_internal, j_internal), {})
                border_css = border_map.get((i_internal - built.nhead if built.nhead else 0, j_internal - 1), "")
                style_str = _build_cell_style(cell_props, border_css)
                escaped_c = escape_html(c)
                if style_str:
                    tr_parts.append(f'<th style="{style_str}">{escaped_c}</th>')
                else:
                    tr_parts.append(f"<th>{escaped_c}</th>")
            head_parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        if head_parts:
            parts.append("<thead>")
            parts.extend(head_parts)
            parts.append("</thead>")

        parts.append("<tbody>")

        covered = self._compute_covered_cells(built.style_grid)
        row_group_positions = built.row_group_positions

        for r, row in enumerate(built.data_body):
            i_internal = r + 1
            tr_parts: list[str] = []
            for c, val in enumerate(row):
                j_internal = c + 1
                if (i_internal, j_internal) in covered:
                    continue
                span_props = built.style_grid.get((i_internal, j_internal), {})
                colspan = span_props.get("colspan", 1)
                rowspan = span_props.get("rowspan", 1)

                cell_props = built.style_grid.get((i_internal, j_internal), {})
                ti = i_internal - 1
                tj = j_internal - 1
                border_css = border_map.get((ti, tj), "")
                style_str = _build_cell_style(cell_props, border_css)

                is_group_label = i_internal in row_group_positions
                if is_group_label and not style_str:
                    style_str = "font-weight:bold;background-color:#f0f0f0"

                tag = "th" if i_internal <= 0 else "td"

                attrs = []
                if colspan > 1:
                    attrs.append(f'colspan="{colspan}"')
                if rowspan > 1:
                    attrs.append(f'rowspan="{rowspan}"')

                cell_content = val

                attr_str = " ".join(attrs)
                if style_str:
                    if attr_str:
                        tr_parts.append(f'<{tag} style="{style_str}" {attr_str}>{cell_content}</{tag}>')
                    else:
                        tr_parts.append(f'<{tag} style="{style_str}">{cell_content}</{tag}>')
                else:
                    if attr_str:
                        tr_parts.append(f'<{tag} {attr_str}>{cell_content}</{tag}>')
                    else:
                        tr_parts.append(f"<{tag}>{cell_content}</{tag}>")
            if tr_parts:
                parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        parts.append("</tbody>")

        notes = built.notes
        if notes:
            parts.append("<tfoot>")
            for note in notes:
                escaped = escape_html(note.text)
                if note.marker:
                    escaped_marker = escape_html(note.marker)
                    parts.append(
                        f'<tr><td colspan="{ncol}" style="text-align:left">'
                        f"<sup>{escaped_marker}</sup> {escaped}</td></tr>"
                    )
                else:
                    parts.append(
                        f'<tr><td colspan="{ncol}" style="text-align:left">{escaped}</td></tr>'
                    )
            parts.append("</tfoot>")

        parts.append("</table>")
        return "\n".join(parts)

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
