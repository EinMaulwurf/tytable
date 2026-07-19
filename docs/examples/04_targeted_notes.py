"""Targeted notes — automatic numbering, explicit markers, and list selectors."""

import polars as pl

from tytable import NoteDict, tt

df = pl.DataFrame(
    {
        "Region": ["North", "South", "West"],
        "Actual": [128, 117, 136],
        "Forecast": [125, 121, 136],
    }
)

actual_note: NoteDict = {
    "text": "Actual includes a one-time contract.",
    "i": 0,
    "j": "Actual",
}

# This constructor form is identical to the annotated dictionary above.
forecast_note = NoteDict(
    text="Forecast values are provisional.",
    marker="*",
    i=[0, 1, 2],
    j="Forecast",
)

(
    tt(
        df,
        caption="Quarterly revenue (USD thousands)",
        notes=[
            actual_note,
            forecast_note,
            "Source: Finance planning model.",
        ],
    )
    .theme_striped()
    .style(i="header", bold=True)
    .style(i="notes", italic=True, color="#52606d")
    .save("build/04_targeted_notes.typ")
)
