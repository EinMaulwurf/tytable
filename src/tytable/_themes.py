"""
Built-in theme registry and the theme functions behind it.

Each theme is a callable ``theme(table) -> TyTable`` that records style
directives and/or Typst options on the table. The ``THEMES`` dict maps the
public names (``"default"``, ``"striped"``, …) to these callables.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import fields
from typing import TYPE_CHECKING

from ._render_typst import TypstRenderOptions

if TYPE_CHECKING:
    from ._tytable import TyTable


def default_line_color(table: TyTable) -> str:
    """Return the default rule color (always black)."""
    return "black"


def theme_default(table: TyTable) -> TyTable:
    """Apply the booktab-style default theme: thin top/bottom rules under the header."""
    col = default_line_color(table)

    def prepare(t: TyTable) -> None:
        last = t._n_merged_body_rows
        t._deferred_style(i=last - 1, line="b", line_color=col, line_width=0.08)
        n_cg = len(t._col_group_rows)
        if n_cg > 0:
            t._deferred_style(i=-(n_cg), line="t", line_color=col, line_width=0.08)
        elif t._show_colnames:
            t._deferred_style(i="header", line="t", line_color=col, line_width=0.08)
        else:
            t._deferred_style(i=0, line="t", line_color=col, line_width=0.08)
        if t._show_colnames:
            t._deferred_style(i="header", line="b", line_color=col, line_width=0.05)

    table._prepare_hooks.append(prepare)
    theme_typst(table)
    return table


def theme_striped(table: TyTable) -> TyTable:
    """Apply alternating grey background stripes to even data rows."""

    def prepare(t: TyTable) -> None:
        nrows = t._n_merged_body_rows
        even = list(range(0, nrows, 2))
        if even:
            t._deferred_style(i=even, background="#ededed")

    table._prepare_hooks.append(prepare)
    return table


def theme_grid(table: TyTable) -> TyTable:
    """Apply a full grid: black borders around every cell."""
    table._typst_opts.grid_stroke = "(paint: black)"
    table.style(line="tblr", line_color="black", line_width=0.05)
    return table


def theme_empty(table: TyTable) -> TyTable:
    """Strip all styles, formats, prepare-hooks, and Typst options — a blank slate."""
    table._style_directives.clear()
    table._deferred_style_directives.clear()
    table._format_directives.clear()
    table._prepare_hooks.clear()
    table._typst_opts = TypstRenderOptions(figure=table._typst_opts.figure)
    return table


def theme_rotate(
    table: TyTable,
    angle: int = 90,
    i: int | str | Sequence[int | str] | None = None,
    j: int | str | Sequence[int] | Sequence[str] | None = None,
) -> TyTable:
    """Rotate the whole table (``i``/``j`` both ``None``) or just selected cells."""
    if i is None and j is None:
        table._typst_opts.rotate_angle = angle
    else:
        table.fmt(i=i, j=j, fn=lambda v: f"#rotate({-angle}, reflow: true, [{v}])")
    return table


def theme_typst(table: TyTable, **opts: object) -> TyTable:
    """Set raw Typst render options (``figure``, ``multipage``, ``portable``, …)."""
    valid_keys = {field.name for field in fields(TypstRenderOptions)}
    invalid_keys = opts.keys() - valid_keys
    if invalid_keys:
        invalid = ", ".join(sorted(invalid_keys))
        valid = ", ".join(sorted(valid_keys))
        raise ValueError(f"unknown Typst render option(s): {invalid}. Valid options: {valid}")

    for key, value in opts.items():
        if value is not None:
            setattr(table._typst_opts, key, value)
    return table


def theme_resize(
    table: TyTable,
    width: float | None = 1,
    height: float | None = None,
    direction: str = "both",
) -> TyTable:
    """Scale the table to fit a target size (a fraction of the available area).

    Wraps the rendered Typst fragment in a ``#layout(size => …)`` block that
    measures the table and rescales it by a uniform factor.

    Parameters
    ----------
    width
        Target width as a fraction of the page content width (``1`` = full
        width). Used unless ``height`` is given. Defaults to ``1``.
    height
        Target height as a fraction of the page content height. When set,
        height drives the scaling and width follows proportionally.
    direction
        ``"down"`` only shrink oversized tables, ``"up"`` only expand
        undersized ones, ``"both"`` (default) always scale to the target.
    """
    table._typst_opts.resize_width = width
    table._typst_opts.resize_height = height
    table._typst_opts.resize_direction = direction
    return table


THEMES = {
    "default": theme_default,
    "grid": theme_grid,
    "striped": theme_striped,
    "empty": theme_empty,
    "rotate": theme_rotate,
    "resize": theme_resize,
}
