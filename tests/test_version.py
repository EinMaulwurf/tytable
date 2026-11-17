"""Also run standalone against isolated wheel/sdist installs in release CI."""

import os
from importlib.metadata import version

import tytable


def test_runtime_version_matches_installed_metadata():
    installed = version("tytable")
    assert tytable.__version__ == installed, (
        f"Version mismatch: tytable.__version__={tytable.__version__!r}, "
        f"installed metadata={installed!r}. Run `make install` to refresh the "
        "editable build; do not edit the generated _version.py."
    )


def test_release_version_matches_tag_when_requested():
    expected = os.environ.get("TYTABLE_EXPECTED_VERSION")
    if expected is None:
        return
    installed = version("tytable")
    assert tytable.__version__ == installed == expected, (
        f"Release version mismatch: expected tag version={expected!r}, "
        f"tytable.__version__={tytable.__version__!r}, metadata={installed!r}. "
        "Rebuild from the release tag with complete Git history and tags."
    )
