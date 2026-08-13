"""
HTML renderer — produces a self-contained ``<table>`` for Jupyter previews.

Used by :meth:`TyTable._repr_html_` and by ``.render("html")`` / ``.save("*.html")``.
"""

from __future__ import annotations

from typing import Any

from ._colors import color_to_css
from ._escape import escape_html
from ._groups import _resolve_col_group_spans
from ._renderer import Renderer
from ._resolve import BuiltTable
from ._style_markup import StyleMarkup, align_to_css
from ._styling import compute_covered_cells, resolve_line_edges


def _align_to_css(h: str | None, v: str | None) -> str | None:
    """Translate alignment shorthands into a CSS ``text-align`` keyword string."""
    return align_to_css(h, v)


def _style_html_inline(props: dict[str, Any], content: str) -> str:
    """Wrap escaped HTML ``content`` with inline caption/notes styling.

    Mirrors tinytable's ``style_string_html``: composable CSS properties
    (color, font-size, small-caps, mono, indent) go into a single ``<span>``,
    then non-CSS decorations (italic, strikeout, underline, bold) wrap it.
    """
    return StyleMarkup.from_props(props).html_inline(content)


def _build_cell_style(cell_props: dict[str, Any], border_css: str) -> str:
    """Build a single CSS style attribute string from cell props and pre-computed border CSS."""
    return StyleMarkup.from_props(cell_props).html_cell_css(border_css)


def _with_default_alignment(
    props: dict[str, Any], alignment: str, *, row_group: bool = False
) -> dict[str, Any]:
    """Add an inferred alignment without overriding an explicit cell style."""
    if "align" in props or row_group or alignment == "l":
        return props
    return {**props, "align": alignment}


def _build_border_map(
    style_lines: list[dict[str, Any]], style_grid: dict[tuple[int, int], dict[str, Any]]
) -> dict[tuple[int, int], str]:
    """Collapse ``line=`` directives into a ``{(row, col): "border-top:…;border-left:…;"}`` map."""
    cell_borders: dict[tuple[int, int], dict[str, str]] = {}
    covered_by: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    for (row, col), props in style_grid.items():
        colspan = props.get("colspan", 1)
        rowspan = props.get("rowspan", 1)
        if colspan > 1 or rowspan > 1:
            for covered_row in range(row, row + rowspan):
                for covered_col in range(col, col + colspan):
                    if (covered_row, covered_col) != (row, col):
                        covered_by[(covered_row, covered_col)] = (row, col, rowspan, colspan)
    css_style = {
        "solid": "solid",
        "dashed": "dashed",
        "dotted": "dotted",
        "dash-dotted": "dashed",
    }
    for entry in resolve_line_edges(style_lines).values():
        ti = entry["cell_i"]
        tj = entry["cell_j"]
        width = entry.get("line_width", 0.1)
        line_color = color_to_css(entry.get("line_color", "black"))
        line_style = entry.get("line_style", "solid")
        value = (
            "none" if line_style == "none" else f"{width}em {css_style[line_style]} {line_color}"
        )
        side = {"t": "top", "b": "bottom", "l": "left", "r": "right"}[entry["side"]]
        if (ti, tj) in covered_by:
            row, col, rowspan, colspan = covered_by[(ti, tj)]
            on_outer_edge = (
                (side == "top" and ti == row)
                or (side == "bottom" and ti == row + rowspan - 1)
                or (side == "left" and tj == col)
                or (side == "right" and tj == col + colspan - 1)
            )
            if not on_outer_edge:
                continue
            ti, tj = row, col
        cell_borders.setdefault((ti, tj), {})[side] = value

    order = ("top", "bottom", "left", "right")
    return {
        cell: "".join(f"border-{side}:{borders[side]};" for side in order if side in borders)
        for cell, borders in cell_borders.items()
    }


class HtmlRenderer(Renderer):
    """Render a :class:`BuiltTable` to an HTML ``<table>`` string."""

    def render(self, built: BuiltTable) -> str:
        """Produce the full ``<table>…</table>`` HTML (colgroup, thead, tbody, tfoot)."""
        ncol = len(built.colnames_display)
        border_map = _build_border_map(built.style_lines, built.style_grid)
        parts = [self._table_open(built)]
        self._emit_caption(parts, built)
        self._emit_colgroup(parts, built)
        self._emit_header(parts, built, border_map)
        self._emit_body(parts, built, border_map)
        self._emit_footer(parts, built, ncol)
        parts.append("</table>")
        return "\n".join(parts)

    @staticmethod
    def _table_open(built: BuiltTable) -> str:
        """Return the opening table tag with width styling."""
        table_style = "border-collapse:collapse;font-family:sans-serif;font-size:1em"
        if built.width is not None and isinstance(built.width, (int, float)):
            table_style += f";width:{built.width * 100:.2f}%"
        elif isinstance(built.width, str):
            table_style += f";width:{built.width}"
        return f'<table style="{table_style}">'

    @staticmethod
    def _emit_colgroup(parts: list[str], built: BuiltTable) -> None:
        """Append the optional HTML ``colgroup`` width declarations."""
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

    @staticmethod
    def _emit_caption(parts: list[str], built: BuiltTable) -> None:
        """Append the escaped and styled caption when present."""
        if built.caption is not None:
            escaped = escape_html(built.caption)
            attrs = ""
            if built.style_caption:
                escaped = _style_html_inline(built.style_caption, escaped)
                align = _align_to_css(built.style_caption.get("align"), None)
                if align:
                    attrs = f' style="text-align:{align}"'
            parts.append(f"<caption{attrs}>{escaped}</caption>")

    def _emit_header(
        self,
        parts: list[str],
        built: BuiltTable,
        border_map: dict[tuple[int, int], str],
    ) -> None:
        """Append column-group and column-name header rows."""
        head_parts: list[str] = []
        head_parts.extend(self._col_group_rows(built, border_map))
        if built.show_colnames:
            head_parts.append(self._column_name_row(built, border_map))

        if head_parts:
            parts.append("<thead>")
            parts.extend(head_parts)
            parts.append("</thead>")

    @staticmethod
    def _col_group_rows(built: BuiltTable, border_map: dict[tuple[int, int], str]) -> list[str]:
        """Build HTML rows for resolved column-group spans."""
        rows: list[str] = []
        for display_row, cg_row in enumerate(built.col_groups):
            cells: list[str] = []
            for label, start, span in _resolve_col_group_spans(cg_row):
                escaped = escape_html(label) if label else ""
                colspan = f' colspan="{span}"' if span > 1 else ""
                props = {"align": "c", **built.style_grid.get((display_row, start), {})}
                style = _build_cell_style(props, border_map.get((display_row, start), ""))
                style_attr = f' style="{style}"' if style else ""
                cells.append(f"<th{colspan}{style_attr}>{escaped}</th>")
            rows.append(f"<tr>{' '.join(cells)}</tr>")
        return rows

    @staticmethod
    def _column_name_row(built: BuiltTable, border_map: dict[tuple[int, int], str]) -> str:
        """Build the styled column-name header row."""
        cells: list[str] = []
        display_row = built.layout.header_row
        if display_row is None:
            return ""
        covered = compute_covered_cells(built.style_grid)
        for j, colname in enumerate(built.colnames_display):
            if (display_row, j) in covered:
                continue
            cell_props = _with_default_alignment(
                built.style_grid.get((display_row, j), {}), built.column_alignments[j]
            )
            border_css = border_map.get((display_row, j), "")
            style = _build_cell_style(cell_props, border_css)
            attrs = HtmlRenderer._span_attrs(cell_props)
            cells.append(HtmlRenderer._cell("th", colname, style, attrs))
        return f"<tr>{' '.join(cells)}</tr>"

    @staticmethod
    def _emit_body(
        parts: list[str],
        built: BuiltTable,
        border_map: dict[tuple[int, int], str],
    ) -> None:
        """Append visible body rows, respecting spans and row-group styling."""
        parts.append("<tbody>")
        covered = compute_covered_cells(built.style_grid)
        groupi_rows = set(built.layout.groupi_rows)
        for r, row in enumerate(built.data_body):
            display_row = built.layout.header_rows + r
            is_group = display_row in groupi_rows
            cells: list[str] = []
            for c, val in enumerate(row):
                if (display_row, c) in covered:
                    continue
                cell_props = _with_default_alignment(
                    built.style_grid.get((display_row, c), {}),
                    built.column_alignments[c],
                    row_group=is_group,
                )
                style = _build_cell_style(cell_props, border_map.get((display_row, c), ""))
                if is_group and not style:
                    style = "font-weight:bold;background-color:#f0f0f0"
                attrs = HtmlRenderer._span_attrs(cell_props)
                cells.append(HtmlRenderer._cell("td", val, style, attrs))
            if cells:
                parts.append(f"<tr>{' '.join(cells)}</tr>")
        parts.append("</tbody>")

    @staticmethod
    def _span_attrs(props: dict[str, Any]) -> list[str]:
        """Return HTML span attributes for a resolved cell style."""
        attrs: list[str] = []
        if props.get("colspan", 1) > 1:
            attrs.append(f'colspan="{props["colspan"]}"')
        if props.get("rowspan", 1) > 1:
            attrs.append(f'rowspan="{props["rowspan"]}"')
        return attrs

    @staticmethod
    def _cell(tag: str, content: str, style: str = "", attrs: list[str] | None = None) -> str:
        """Build one HTML table cell with stable attribute ordering."""
        attr_text = " ".join(attrs or [])
        if style:
            attr_text = f'style="{style}"' + (f" {attr_text}" if attr_text else "")
        prefix = f" {attr_text}" if attr_text else ""
        return f"<{tag}{prefix}>{content}</{tag}>"

    @staticmethod
    def _emit_footer(parts: list[str], built: BuiltTable, ncol: int) -> None:
        """Append styled footnote rows when present."""
        if not built.notes:
            return
        note_style = built.style_notes
        align = _align_to_css(note_style.get("align"), None) or "left"
        css = [f"text-align:{align}"]
        alignv = _align_to_css(None, note_style.get("alignv"))
        if alignv:
            css.append(f"vertical-align:{alignv}")
        if note_style.get("background"):
            css.append(f"background-color:{color_to_css(note_style['background'])}")
        if note_style.get("indent") and note_style["indent"] > 0:
            css.append(f"padding-left:{note_style['indent']}em")
        td_style = ";".join(css)
        parts.append("<tfoot>")
        for note in built.notes:
            content = escape_html(note.text)
            if note_style:
                content = _style_html_inline(note_style, content)
            if note.marker:
                content = f"<sup>{escape_html(note.marker)}</sup> {content}"
            parts.append(f'<tr><td colspan="{ncol}" style="{td_style}">{content}</td></tr>')
        parts.append("</tfoot>")
