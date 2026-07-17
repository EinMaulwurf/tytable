"""Static-image example — no Matplotlib or optional image dependencies needed."""

import polars as pl

from tytable import tt

flags = pl.DataFrame(
    {
        "Flag": ["DE", "FR", "IT"],
        "Country": ["Germany", "France", "Italy"],
        "Capital": ["Berlin", "Paris", "Rome"],
    }
)

(
    tt(flags, caption="Existing SVG files embedded without plotting dependencies")
    .images(
        j="Flag",
        # Paths resolve from build/07_static_images.typ, not this Python file.
        paths=[
            "../assets/flags/de.svg",
            "../assets/flags/fr.svg",
            "../assets/flags/it.svg",
        ],
        height=1.2,
    )
    .style(i="header", bold=True, line="b")
    .save("build/07_static_images.typ")
)
