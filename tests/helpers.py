import os
import pathlib

SNAP = pathlib.Path(__file__).parent / "snapshots"


def assert_snapshot(name: str, actual: str) -> None:
    """Compare `actual` to stored snapshot tests/snapshots/{name}.txt.

    If the snapshot does not exist, or env SNAPSHOT_UPDATE is set, write it.
    Otherwise assert byte equality with a helpful diff.
    """
    SNAP.mkdir(parents=True, exist_ok=True)
    path = SNAP / f"{name}.txt"
    if not path.exists() or os.environ.get("SNAPSHOT_UPDATE"):
        path.write_text(actual)
        return
    expected = path.read_text()
    assert actual == expected, _diff(expected, actual)


def _diff(expected: str, actual: str) -> str:
    import difflib

    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        actual.splitlines(keepends=True),
        fromfile="expected",
        tofile="actual",
        n=3,
    )
    return "".join(diff)
