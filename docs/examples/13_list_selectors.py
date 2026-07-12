"""
List selectors — targeting multiple rows and columns by name in one call.

``i`` and ``j`` both accept a list of strings, so you can apply the same
formatting or styling to several columns or rows without repeating yourself.
Unlike integer lists, string lists read as plain-language descriptions:
``j=["Revenue", "Cost"]`` instead of ``j=[0, 2]``.

This example uses a list-of-strings ``j`` selector to align and format every
numeric column in one ``.style()`` call and one ``.fmt()`` call, and a
list-of-strings ``i`` selector to make both the column-header row and all data
rows bold at once.
"""

import polars as pl

from tytable import tt

df = pl.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Gizmo", "Thing"],
        "Revenue": [12450.5, 9800.0, 15200.25, 7300.75],
        "Cost": [8100.0, 6200.0, 9900.0, 5100.0],
        "Growth %": [12.3, -3.1, 18.7, 5.2],
    }
)

(
    tt(df, caption="List selectors — strings as row/column targets", width=1)
    .style(i=["header", "body"], bold=True)
    .style(j=["Revenue", "Cost", "Growth %"], align="r")
    .fmt(j=["Revenue", "Cost"], digits=0)
    .fmt(j=["Growth %"], digits=1)
    .style(i="header", background="#2c3e50", color="white")
    .save("build/13_list_selectors.typ")
)
