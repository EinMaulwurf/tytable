from __future__ import annotations

from typing import TYPE_CHECKING

from ._render_typst import TypstRenderOptions

if TYPE_CHECKING:
    from ._tinytable import TinyTable


def default_line_color(table: TinyTable) -> str:
    return "black"


def theme_default(table: TinyTable) -> TinyTable:
    col = default_line_color(table)

    def prepare(t: TinyTable) -> None:
        last = t._n_merged_body_rows
        t.style(i=last - 1, line="b", line_color=col, line_width=0.08)
        n_cg = len(t._col_group_rows)
        if n_cg > 0:
            t.style(i=-(n_cg), line="t", line_color=col, line_width=0.08)
        elif t._show_colnames:
            t.style(i="header", line="t", line_color=col, line_width=0.08)
        else:
            t.style(i=0, line="t", line_color=col, line_width=0.08)
        if t._show_colnames:
            t.style(i="header", line="b", line_color=col, line_width=0.05)

    table._prepare_hooks.append(prepare)
    theme_typst(table)
    return table


def theme_striped(table: TinyTable) -> TinyTable:
    def prepare(t: TinyTable) -> None:
        nrows = t._n_merged_body_rows
        even = list(range(0, nrows, 2))
        if even:
            t.style(i=even, background="#ededed")

    table._prepare_hooks.append(prepare)
    return table


def theme_grid(table: TinyTable) -> TinyTable:
    table._typst_opts.grid_stroke = "(paint: black)"
    table.style(line="tblr", line_color="black", line_width=0.05)
    return table


def theme_empty(table: TinyTable) -> TinyTable:
    table._style_directives.clear()
    table._format_directives.clear()
    table._prepare_hooks.clear()
    table._typst_opts = TypstRenderOptions()
    return table


def theme_rotate(
    table: TinyTable,
    angle: int = 90,
    i: int | str | list[int] | None = None,
    j: int | str | list[int] | None = None,
) -> TinyTable:
    if i is None and j is None:
        table._typst_opts.rotate_angle = angle
    else:
        table.fmt(i=i, j=j, fn=lambda v: f"#rotate({-angle}, reflow: true, [{v}])")
    return table


def theme_typst(table: TinyTable, **opts: object) -> TinyTable:
    for key, value in opts.items():
        if value is not None:
            setattr(table._typst_opts, key, value)
    return table


THEMES = {
    "default": theme_default,
    "grid": theme_grid,
    "striped": theme_striped,
    "empty": theme_empty,
    "rotate": theme_rotate,
}
