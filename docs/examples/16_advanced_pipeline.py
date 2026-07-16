"""Reusable report component — type-safe configuration around ``TyTable``."""

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from tytable import TyTable, tt


@dataclass(frozen=True)
class ReportStyle:
    """A small design token set shared by every table in a report."""

    ink: str = "#17324d"
    accent: str = "#087e8b"
    pale: str = "#eaf6f6"
    warning: str = "#b23a48"


def apply_report_style(table: TyTable, style: ReportStyle) -> TyTable:
    """A typed theme function: accept and return the public ``TyTable`` class."""

    return (
        table.style(i="header", bold=True, color="white", background=style.ink)
        .style(i="groupj", bold=True, color=style.ink, background=style.pale)
        .style(i="caption", bold=True, color=style.ink, fontsize=1.15)
        .style(i="notes", italic=True, color="#52606d")
    )


class QuarterlyReportTable:
    """Turn a raw frame into the project's standard quarterly table."""

    def __init__(self, data: pl.DataFrame, style: ReportStyle | None = None) -> None:
        self.data = data
        self.style = style or ReportStyle()

    def build(self) -> TyTable:
        numeric = ["Revenue", "Target", "Variance"]
        table = (
            tt(
                self.data,
                caption="Quarterly performance",
                label="quarterly-performance",
                notes=["Variance is actual revenue minus target."],
                width=["3.2cm", "1fr", "1fr", "1fr"],
            )
            .group(j={"Actual": ["Revenue"], "Plan": ["Target", "Variance"]})
            .fmt(j=numeric, digits=0)
            .style(i=pl.col("Variance") < 0, j="Variance", bold=True, color=self.style.warning)
            .style(i=pl.col("Variance") >= 0, j="Variance", bold=True, color=self.style.accent)
        )
        return apply_report_style(table, self.style)

    def save(self, directory: Path) -> None:
        """Keep filesystem policy outside the table-building method."""

        self.build().save(str(directory / "quarterly-performance.typ"))


df = pl.DataFrame(
    {
        "Region": ["North", "South", "East", "West"],
        "Revenue": [1_284_000, 936_000, 1_512_000, 1_067_000],
        "Target": [1_200_000, 1_000_000, 1_450_000, 1_100_000],
    }
).with_columns((pl.col("Revenue") - pl.col("Target")).alias("Variance"))

QuarterlyReportTable(df).build().save("build/16_advanced_pipeline.typ")
