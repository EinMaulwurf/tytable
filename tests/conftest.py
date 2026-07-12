import pytest


@pytest.fixture(autouse=True)
def _deterministic_ids(monkeypatch):
    """
    Inject a deterministic image-id generator so snapshots are reproducible.

    Targets the canonical location `tytable._utils._new_image_id` and any
    per-module overrides added later (`tytable._images._new_image_id`,
    `tytable._plots._new_image_id`). Modules that don't exist yet are
    skipped silently.
    """
    counter = {"n": 0}

    def fake_id() -> str:
        counter["n"] += 1
        return f"testid{counter['n']:04d}"

    import importlib

    for modname, attr in (
        ("tytable._utils", "_new_image_id"),
        ("tytable._images", "_new_image_id"),
        ("tytable._plots", "_new_image_id"),
    ):
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            continue
        if hasattr(mod, attr):
            monkeypatch.setattr(mod, attr, fake_id)
