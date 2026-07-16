"""
HTML renderer — produces a self-contained ``<table>`` for Jupyter previews.

Used by :meth:`TyTable._repr_html_` and by ``.render("html")`` / ``.save("*.html")``.
"""

from __future__ import annotations

from typing import Any

from ._escape import escape_html
from ._groups import _resolve_col_group_spans
from ._indices import convert_col_to_typst, convert_row_to_typst
from ._renderer import Renderer
from ._resolve import BuiltTable
from ._style_markup import StyleMarkup, align_to_css
from ._styling import compute_covered_cells


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


def _build_border_map(style_lines: list[dict[str, Any]], nhead: int) -> dict[tuple[int, int], str]:
    """Collapse ``line=`` directives into a ``{(row, col): "border-top:…;border-left:…;"}`` map."""
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
        parts = [self._table_open(built)]
        self._emit_colgroup(parts, built)
        self._emit_caption(parts, built)
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
            if built.style_caption:
                escaped = _style_html_inline(built.style_caption, escaped)
            parts.append(f"<caption>{escaped}</caption>")

    def _emit_header(
        self,
        parts: list[str],
        built: BuiltTable,
        border_map: dict[tuple[int, int], str],
    ) -> None:
        """Append column-group and column-name header rows."""
        head_parts: list[str] = []
        head_parts.extend(self._col_group_rows(built))
        if built.show_colnames:
            head_parts.append(self._column_name_row(built, border_map))

        if head_parts:
            parts.append("<thead>")
            parts.extend(head_parts)
            parts.append("</thead>")

    @staticmethod
    def _col_group_rows(built: BuiltTable) -> list[str]:
        """Build HTML rows for resolved column-group spans."""
        rows: list[str] = []
        for cg_row in built.col_groups:
            cells: list[str] = []
            for label, _start, span in _resolve_col_group_spans(cg_row):
                if not label:
                    cells.append("<th></th>")
                    continue
                escaped = escape_html(label)
                colspan = f' colspan="{span}"' if span > 1 else ""
                cells.append(f'<th{colspan} style="text-align:center">{escaped}</th>')
            rows.append(f"<tr>{' '.join(cells)}</tr>")
        return rows

    @staticmethod
    def _column_name_row(built: BuiltTable, border_map: dict[tuple[int, int], str]) -> str:
        """Build the styled column-name header row."""
        cells: list[str] = []
        ti = convert_row_to_typst(0, built.nhead)
        for j, colname in enumerate(built.colnames_display):
            j_internal = j + 1
            cell_props = _with_default_alignment(
                built.style_grid.get((0, j_internal), {}), built.column_alignments[j]
            )
            border_css = border_map.get((ti, j), "")
            style = _build_cell_style(cell_props, border_css)
            cells.append(HtmlRenderer._cell("th", colname, style))
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
        for r, row in enumerate(built.data_body):
            i_internal = r + 1
            cells: list[str] = []
            for c, val in enumerate(row):
                j_internal = c + 1
                if (i_internal, j_internal) in covered:
                    continue
                cell_props = _with_default_alignment(
                    built.style_grid.get((i_internal, j_internal), {}),
                    built.column_alignments[c],
                    row_group=i_internal in built.row_group_positions,
                )
                ti = convert_row_to_typst(i_internal, built.nhead)
                style = _build_cell_style(cell_props, border_map.get((ti, c), ""))
                if i_internal in built.row_group_positions and not style:
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
        align = _align_to_css(note_style.get("align"), note_style.get("alignv")) or "left"
        css = [f"text-align:{align}"]
        if note_style.get("background"):
            css.append(f"background-color:{note_style['background']}")
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
