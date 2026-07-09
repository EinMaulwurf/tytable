from __future__ import annotations

import pathlib

import polars as pl

from ._directives import StyleDirective
from ._groups import register_col_groups, register_row_groups
from ._render_typst import TypstRenderer, TypstRenderOptions
from ._resolve import build
from ._styling import _validate_style


def tt(
    data,
    *,
    caption=None,
    notes=None,
    width=None,
    height=None,
    colnames=True,
    colnames_override=None,
    rownames=False,
    digits=None,
    escape=True,
    theme="default",
) -> TinyTable:
    return TinyTable(
        data,
        caption=caption,
        notes=notes,
        width=width,
        height=height,
        colnames=colnames,
        colnames_override=colnames_override,
        rownames=rownames,
        digits=digits,
        escape=escape,
        theme=theme,
    )


class TinyTable:
    def __init__(
        self,
        data: pl.DataFrame,
        *,
        caption: str | None = None,
        notes: list | None = None,
        width: float | list[float] | None = None,
        height: float | None = None,
        colnames: bool = True,
        colnames_override: dict[str, str] | None = None,
        rownames: bool = False,
        digits: int | None = None,
        escape: bool = True,
        theme: str | None = "default",
    ):
        self._data = data.clone()
        if colnames_override:
            self._colnames = [colnames_override.get(c, c) for c in data.columns]
        else:
            self._colnames = list(data.columns)
        self._show_colnames = colnames
        self._caption = caption
        self._width = width
        self._height = height
        self._escape = escape
        self._rownames = rownames
        self._digits = digits
        self._theme = theme

        self._style_directives: list = []
        self._format_directives: list = []
        self._plot_directives: list = []
        self._row_groups: list = []
        self._col_group_rows: list = []
        self._notes: list = list(notes) if notes else []
        self._prepare_hooks: list = []

    def style(
        self,
        i=None,
        j=None,
        *,
        bold=None,
        italic=None,
        underline=None,
        strikeout=None,
        monospace=None,
        smallcaps=None,
        color=None,
        background=None,
        fontsize=None,
        align=None,
        alignv=None,
        indent=None,
        colspan=None,
        rowspan=None,
        line=None,
        line_color=None,
        line_width=0.1,
        line_trim=None,
        output=None,
    ):
        _validate_style(
            align=align, alignv=alignv, line=line, color=color,
            background=background, line_color=line_color,
            colspan=colspan, rowspan=rowspan, line_width=line_width,
            fontsize=fontsize, indent=indent,
        )
        self._style_directives.append(
            StyleDirective(
                i=i, j=j, bold=bold, italic=italic, underline=underline,
                strikeout=strikeout, monospace=monospace, smallcaps=smallcaps,
                color=color, background=background, fontsize=fontsize, align=align,
                alignv=alignv, indent=indent, colspan=colspan, rowspan=rowspan,
                line=line, line_color=line_color, line_width=line_width,
                line_trim=line_trim, output=output,
            )
        )
        return self

    def group(self, i=None, j=None):
        if i is not None:
            register_row_groups(self, i)
        if j is not None:
            register_col_groups(self, j, self._colnames)
        return self

    def render(self, output: str = "typst") -> str:
        built = build(self, output)
        opts = TypstRenderOptions(figure=True, multipage=False)
        return TypstRenderer().render(built, opts)

    def save(self, path: str) -> None:
        p = pathlib.Path(path)
        suffix = p.suffix.lower()
        output = "html" if suffix in (".html", ".htm") else "typst"
        p.write_text(self.render(output), encoding="utf-8")
