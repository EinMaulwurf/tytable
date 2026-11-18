import polars as pl
import pytest

from tytable import tt
from tytable.selectors import colgroup, groupj, rowgroup


def test_explain_resolves_grouped_selectors_and_where():
    table = (
        tt(pl.DataFrame({"a": [1, 3, 0], "b": [5, 1, 9]}))
        .group(i={"first": 0, "second": 2}, j={"values": ["a", "b"]})
        .fmt(i=rowgroup(label="first"), j=colgroup(label="values", level=0), where=pl.all() > 2)
        .style(i=groupj(), bold=True)
        .style(i="data", j="a", where=pl.col("a") > 10, bold=True)
    )

    assert table.explain().splitlines() == [
        "TyTable directives for 'typst'",
        ".fmt() #1  rows=[3, 4] columns=['a', 'b'] where={'b': [3], 'a': [4]}  targets=2",
        ".style() #1  rows=[0] columns=['a', 'b']  targets=1",
        ".style() #2  rows=[3, 4, 6] columns=['a'] where={}  targets=0 (empty selection)",
    ]


def test_explain_skips_filtered_selectors_and_render_work(tmp_path, monkeypatch):
    def fail(*args):
        pytest.fail("explain ran a skipped selector or rendering callback")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tytable._images._require_plotting", fail)
    monkeypatch.setattr("tytable._images._static_image_bytes", fail)
    table = (
        tt(pl.DataFrame({"value": [1, 2]}))
        .fmt(i=fail, fn=fail, output="typst")
        .fmt(i=lambda row: row["value"] == 1, fn=fail)
        .plot(j="value", fn=fail)
        .images(i=0, j="value", paths=["missing.png"])
        .style(i=fail, bold=True, output="ascii")
        .finalize(fail)
    )

    assert table.explain("html").splitlines() == [
        "TyTable directives for 'html'",
        ".fmt() #1  skipped (output=('typst',))",
        ".fmt() #2  rows=[1] columns=['value']  targets=1",
        ".plot() #1  rows=[1, 2] columns=['value']  targets=2",
        ".images() #2  rows=[1] columns=['value']  targets=1",
        ".style() #1  skipped (output=('ascii',))",
    ]
    assert list(tmp_path.iterdir()) == []


def test_explain_counts_notes_metadata_and_hidden_columns():
    table = (
        tt(
            pl.DataFrame({"a": [1], "b": [2]}),
            colnames=False,
            notes=["general", {"text": "targeted", "i": 0, "j": "b"}],
        )
        .group(j={"hidden": ["b"]})
        .show_columns("a")
        .fmt(j="b")
        .style(i=["caption", "notes"], italic=True)
        .style(i=["header", groupj(level=0)], bold=True)
    )

    assert table.explain("ascii").splitlines() == [
        "TyTable directives for 'ascii'",
        ".fmt() #1  rows=[0] columns=['b']  targets=1",
        "notes #1  table note  targets=1",
        "notes #2  rows=[0] columns=['b']  targets=1",
        ".style() #1  rows=[] columns=['a', 'b'] metadata=['caption', 'notes']  targets=2",
        ".style() #2  rows=[] columns=['a', 'b']  targets=0 (empty selection)",
    ]


def test_explain_validates_output_and_active_selectors():
    table = tt(pl.DataFrame({"a": [1]}))
    assert table.explain().endswith("No directives recorded")
    with pytest.raises(NotImplementedError, match="output='pdf'"):
        table.explain("pdf")
    table.plot(i="header", j="a", fn=lambda _: None)
    with pytest.raises(ValueError, match=r"\.plot\(\) cannot target.*header"):
        table.explain()
