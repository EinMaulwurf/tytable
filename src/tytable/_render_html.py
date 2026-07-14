"""
HTML renderer — produces a self-contained ``<table>`` for Jupyter previews.

Used by :meth:`TinyTable._repr_html_` and by ``.render("html")`` / ``.save("*.html")``.
"""

from __future__ import annotations

from typing import Any

from ._escape import escape_html
from ._groups import _resolve_col_group_spans
from ._renderer import Renderer
from ._resolve import BuiltTable
from ._styling import compute_covered_cells


def _align_to_css(h: str | None, v: str | None) -> str | None:
    """Translate alignment shorthands into a CSS ``text-align`` keyword string."""
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


def _style_html_inline(props: dict[str, Any], content: str) -> str:
    """Wrap escaped HTML ``content`` with inline caption/notes styling.

    Mirrors tinytable's ``style_string_html``: composable CSS properties
    (color, font-size, small-caps, mono, indent) go into a single ``<span>``,
    then non-CSS decorations (italic, strikeout, underline, bold) wrap it.
    """
    css_parts: list[str] = []
    if props.get("smallcaps"):
        css_parts.append("font-variant:small-caps")
    if "color" in props:
        css_parts.append(f"color:{props['color']}")
    if "fontsize" in props:
        css_parts.append(f"font-size:{props['fontsize']}em")
    if props.get("monospace"):
        css_parts.append("font-family:monospace")
    if props.get("background"):
        css_parts.append(f"background-color:{props['background']}")
    if props.get("indent") and props["indent"] > 0:
        css_parts.append(f"padding-left:{props['indent']}em")
    out = content
    if css_parts:
        out = f'<span style="{";".join(css_parts)}">{out}</span>'
    if props.get("italic"):
        out = f"<i>{out}</i>"
    if props.get("strikeout"):
        out = f"<s>{out}</s>"
    if props.get("underline"):
        out = f"<u>{out}</u>"
    if props.get("bold"):
        out = f"<b>{out}</b>"
    return out


def _build_cell_style(cell_props: dict[str, Any], border_css: str) -> str:
    """Build a single CSS style attribute string from cell props and pre-computed border CSS."""
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
    if "rotate" in cell_props:
        css_parts.append(f"transform:rotate({cell_props['rotate']}deg)")
        css_parts.append("white-space:nowrap")

    align = _align_to_css(
        cell_props.get("align"),
        cell_props.get("alignv"),
    )
    if align:
        css_parts.append(f"text-align:{align}")

    return "; ".join(css_parts) if css_parts else ""


def _build_border_map(style_lines: list[dict[str, Any]], nhead: int) -> dict[tuple[int, int], str]:
    """Collapse ``line=`` directives into a ``{(row, col): "border-top:…;border-left:…;"}`` map."""
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


class HtmlRenderer(Renderer):
    """Render a :class:`BuiltTable` to an HTML ``<table>`` string."""

    def render(self, built: BuiltTable) -> str:
        """Produce the full ``<table>…</table>`` HTML (colgroup, thead, tbody, tfoot)."""
        ncol = len(built.colnames_display)
        border_map = _build_border_map(built.style_lines, built.nhead)

        parts: list[str] = []
        table_style = "border-collapse:collapse;font-family:sans-serif;font-size:1em"
        if built.width is not None and isinstance(built.width, (int, float)):
            table_style += f";width:{built.width * 100:.2f}%"
        elif isinstance(built.width, str):
            table_style += f";width:{built.width}"
        parts.append(f'<table style="{table_style}">')

        if built.width is not None and isinstance(built.width, (list, tuple)):
            colgroup = ["<colgroup>"]
            for w in built.width:
                if w is None:
                    colgroup.append("<col>")
                elif isinstance(w, str):
                    colgroup.append(f'<col style="width:{w}">')
                else:
                    colgroup.append(f'<col style="width:{w * 100:.2f}%">')
            colgroup.append("</colgroup>")
            parts.append("\n".join(colgroup))

        if built.caption is not None:
            escaped = escape_html(built.caption)
            if built.style_caption:
                escaped = _style_html_inline(built.style_caption, escaped)
            parts.append(f"<caption>{escaped}</caption>")

        head_parts: list[str] = []
        if built.col_groups:
            for cg_row in built.col_groups:
                tr_parts: list[str] = []
                for label, _start, span in _resolve_col_group_spans(cg_row):
                    if not label:
                        tr_parts.append("<th></th>")
                        continue
                    escaped_label = escape_html(label)
                    if span > 1:
                        tr_parts.append(
                            f'<th colspan="{span}" style="text-align:center">{escaped_label}</th>'
                        )
                    else:
                        tr_parts.append(f'<th style="text-align:center">{escaped_label}</th>')
                head_parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        if built.show_colnames:
            tr_parts = []
            for j, colname in enumerate(built.colnames_display):
                style_str = ""
                i_internal = 0
                j_internal = j + 1
                cell_props = built.style_grid.get((i_internal, j_internal), {})
                from ._indices import convert_row_to_typst

                ti = convert_row_to_typst(i_internal, built.nhead)
                border_css = border_map.get((ti, j_internal - 1), "")
                style_str = _build_cell_style(cell_props, border_css)
                if style_str:
                    tr_parts.append(f'<th style="{style_str}">{colname}</th>')
                else:
                    tr_parts.append(f"<th>{colname}</th>")
            head_parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        if head_parts:
            parts.append("<thead>")
            parts.extend(head_parts)
            parts.append("</thead>")

        parts.append("<tbody>")

        covered = compute_covered_cells(built.style_grid)
        row_group_positions = built.row_group_positions

        for r, row in enumerate(built.data_body):
            i_internal = r + 1
            tr_parts = []
            for c, val in enumerate(row):
                j_internal = c + 1
                if (i_internal, j_internal) in covered:
                    continue
                span_props = built.style_grid.get((i_internal, j_internal), {})
                colspan = span_props.get("colspan", 1)
                rowspan = span_props.get("rowspan", 1)

                cell_props = built.style_grid.get((i_internal, j_internal), {})
                from ._indices import convert_row_to_typst

                ti = convert_row_to_typst(i_internal, built.nhead)
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
                        tr_parts.append(
                            f'<{tag} style="{style_str}" {attr_str}>{cell_content}</{tag}>'
                        )
                    else:
                        tr_parts.append(f'<{tag} style="{style_str}">{cell_content}</{tag}>')
                else:
                    if attr_str:
                        tr_parts.append(f"<{tag} {attr_str}>{cell_content}</{tag}>")
                    else:
                        tr_parts.append(f"<{tag}>{cell_content}</{tag}>")
            if tr_parts:
                parts.append(f"<tr>{' '.join(tr_parts)}</tr>")

        parts.append("</tbody>")

        notes = built.notes
        if notes:
            note_style = built.style_notes
            align_val = _align_to_css(note_style.get("align"), note_style.get("alignv")) or "left"
            td_css_parts: list[str] = [f"text-align:{align_val}"]
            if note_style.get("background"):
                td_css_parts.append(f"background-color:{note_style['background']}")
            if note_style.get("indent") and note_style["indent"] > 0:
                td_css_parts.append(f"padding-left:{note_style['indent']}em")
            td_style = ";".join(td_css_parts)
            parts.append("<tfoot>")
            for note in notes:
                escaped = escape_html(note.text)
                if note_style:
                    escaped = _style_html_inline(note_style, escaped)
                if note.marker:
                    escaped_marker = escape_html(note.marker)
                    parts.append(
                        f'<tr><td colspan="{ncol}" style="{td_style}">'
                        f"<sup>{escaped_marker}</sup> {escaped}</td></tr>"
                    )
                else:
                    parts.append(f'<tr><td colspan="{ncol}" style="{td_style}">{escaped}</td></tr>')
            parts.append("</tfoot>")

        parts.append("</table>")
        return "\n".join(parts)
