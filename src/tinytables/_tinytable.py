from __future__ import annotations

import pathlib
from collections.abc import Callable

import polars as pl

from ._directives import FormatDirective, Note, PlotDirective, StyleDirective
from ._groups import register_col_groups, register_row_groups
from ._render_typst import TypstRenderer, TypstRenderOptions
from ._resolve import build
from ._styling import _validate_style
from ._themes import THEMES


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
    theme: str | Callable | None = "default",
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


def _normalize_notes(raw) -> list:
    if not raw:
        return []
    result = []
    for item in raw:
        if isinstance(item, Note):
            result.append(item)
        elif isinstance(item, dict):
            result.append(Note(
                text=item.get("text", ""),
                marker=item.get("marker"),
                i=item.get("i"),
                j=item.get("j"),
            ))
        elif isinstance(item, str):
            result.append(Note(text=item))
        else:
            result.append(Note(text=str(item)))
    _assign_markers(result)
    return result


def _assign_markers(notes):
    auto = 0
    for note in notes:
        if note.marker is not None:
            continue
        if note.i is not None or note.j is not None:
            auto += 1
            note = object.__setattr__(note, "marker", str(auto))
        else:
            note = object.__setattr__(note, "marker", None)


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
        theme: str | Callable | None = "default",
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
        self._theme_name = theme

        self._style_directives: list = []
        self._format_directives: list = []
        self._plot_directives: list = []
        self._row_groups: list = []
        self._col_group_rows: list = []
        self._notes: list = _normalize_notes(notes)
        self._prepare_hooks: list = []
        self._assets_dir: str | None = None
        self._assets_relpath: str | None = None

        self._typst_opts = TypstRenderOptions(multipage=False)
        if height is not None:
            self._typst_opts.row_height_em = float(height)

        self._apply_theme(theme)

    def _apply_theme(self, theme: str | Callable | None):
        if theme is None:
            return
        if callable(theme):
            theme(self)
            return
        if isinstance(theme, str):
            fn = THEMES.get(theme)
            if fn is None:
                raise ValueError(f"Unknown theme: {theme!r}. Available: {list(THEMES)}")
            fn(self)
            return

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

    def fmt(
        self,
        i=None,
        j=None,
        *,
        digits=None,
        num_fmt="decimal",
        replace=None,
        escape=False,
        fn=None,
        output=None,
    ):
        self._format_directives.append(
            FormatDirective(
                i=i, j=j, digits=digits, num_fmt=num_fmt,
                replace=replace, escape=escape, fn=fn, output=output,
            )
        )
        return self

    def plot(
        self,
        i=None,
        j=None,
        *,
        fun=None,
        data=None,
        height=1.0,
        height_px=400,
        width_px=1200,
        color="black",
        xlim=None,
        output=None,
    ):
        if j is None:
            raise ValueError(".plot() requires j (column selector)")
        if fun is None:
            raise ValueError(".plot() requires fun (plotting function)")
        if isinstance(height, str):
            height = float(height.replace("em", "").strip())
        self._plot_directives.append(
            PlotDirective(
                i=i, j=j, fun=fun, data=data, color=color, xlim=xlim,
                height=height, height_px=height_px, width_px=width_px,
                output=output,
            )
        )
        return self

    def images(
        self,
        i=None,
        j=None,
        *,
        paths=None,
        height=1.0,
        output=None,
    ):
        if j is None:
            raise ValueError(".images() requires j (column selector)")
        if paths is None:
            raise ValueError(".images() requires paths")
        if isinstance(height, str):
            height = float(height.replace("em", "").strip())
        self._plot_directives.append(
            PlotDirective(
                i=i, j=j, images=list(paths), height=height,
                output=output,
            )
        )
        return self

    def group(self, i=None, j=None):
        if i is not None:
            register_row_groups(self, i)
        if j is not None:
            register_col_groups(self, j, self._colnames)
        return self

    def theme(self, name: str | Callable | None = None):
        self._apply_theme(name)
        self._theme_name = name
        return self

    def render(self, output: str = "typst") -> str:
        built = build(self, output)
        return TypstRenderer().render(built, self._typst_opts)

    def save(self, path: str, assets: str | None = None) -> None:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        if assets is None:
            self._assets_dir = str(p.parent / "tinytable_assets")
            self._assets_relpath = "tinytable_assets"
        else:
            self._assets_dir = str(p.parent / assets)
            self._assets_relpath = assets.replace("\\", "/")

        suffix = p.suffix.lower()
        out = "html" if suffix in (".html", ".htm") else "typst"
        p.write_text(self.render(out), encoding="utf-8")
