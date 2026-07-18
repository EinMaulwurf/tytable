"""Built-in, replaceable base appearances.

Themes are resolved against the semantic table structure during ``build()``.
They therefore never become ordinary user directives and explicit ``style()``
calls always take precedence, regardless of call order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ._indices import _BoundaryRow

if TYPE_CHECKING:
    from ._tytable import TyTable

BaseTheme = Literal["default", "plain", "striped", "grid"]


def apply_base_theme(table: TyTable) -> None:
    """Record the selected base appearance on an isolated build-time table."""
    if table._theme == "plain":
        return
    if table._theme == "striped":
        even_source_rows = list(range(0, table._data.height, 2))
        if even_source_rows:
            table._deferred_style(i=even_source_rows, background="#ededed")
        return
    if table._theme == "grid":
        table._typst_opts.grid_stroke = "(paint: black)"
        table._deferred_style(i="all", line="tblr", line_color="black", line_width=0.05)
        return

    # The default appearance follows actual rendered boundaries.  The private
    # boundary selectors are semantic identities resolved only after grouping.
    last = table._n_merged_body_rows
    if last:
        table._deferred_style(i=_BoundaryRow("last"), line="b", line_color="black", line_width=0.08)
    if table._col_group_rows:
        table._deferred_style(
            i=_BoundaryRow("first"), line="t", line_color="black", line_width=0.08
        )
    elif table._show_colnames:
        table._deferred_style(i="header", line="t", line_color="black", line_width=0.08)
    elif last:
        table._deferred_style(
            i=_BoundaryRow("first"), line="t", line_color="black", line_width=0.08
        )
    if table._show_colnames:
        table._deferred_style(i="header", line="b", line_color="black", line_width=0.05)
