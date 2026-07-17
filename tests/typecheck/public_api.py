"""Static regression checks for public collection annotations."""

from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from tytable import tt


def _accepts_narrow_collection_types(dataframe: pl.DataFrame) -> None:
    """Keep common concrete collections assignable to read-only API inputs."""
    display_names: Mapping[str, str] = {"a": "A"}
    row_labels: list[str] = ["First", "Second"]
    integer_columns: list[int] = [0, 1]
    named_columns: list[str] = ["a", "b"]
    mixed_columns: list[str | int] = [0, "b"]
    mixed_selector: list[str | int] = [0, "b"]
    plot_data: tuple[Any, ...] = ([1, 2], [3, 4])
    integer_limits: list[int] = [0, 10]
    image_paths: tuple[str, ...] = ("a.png", "b.png")

    table = tt(dataframe, colnames_override=display_names)
    table.group(i=row_labels)
    table.group(j={"Integer": integer_columns})
    table.group(j={"Named": named_columns})
    table.group(j={"Mixed": mixed_columns})
    table.style(j=mixed_selector, bold=True)
    table.fmt(j=mixed_selector, digits=1)
    table.theme_rotate(j=mixed_selector)
    table.plot(j=0, fun=lambda value: value, data=plot_data, xlim=integer_limits)
    table.images(j=0, paths=image_paths)


def _accepts_abstract_collection_types(
    dataframe: pl.DataFrame,
    row_labels: Sequence[object],
    column_groups: Mapping[str, Sequence[str | int]],
) -> None:
    """Keep abstract read-only collections valid for grouping."""
    tt(dataframe).group(i=row_labels, j=column_groups)
