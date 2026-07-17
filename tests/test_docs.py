import json
import re
from pathlib import Path

from docs.build_examples import (
    DOCUMENTED_API,
    format_api_signature,
    write_api_signatures,
    write_color_reference,
    write_meta,
)


def test_api_signature_file_covers_every_reference(tmp_path: Path) -> None:
    output = tmp_path / "api.json"
    write_api_signatures(output)

    signatures = json.loads(output.read_text(encoding="utf-8"))
    main_typ = Path("docs/main.typ").read_text(encoding="utf-8")
    references = set(re.findall(r'api_signatures\.at\("([a-z_]+)"\)', main_typ))

    assert references == set(DOCUMENTED_API)
    assert signatures == {
        key: format_api_signature(display_name, callable_)
        for key, (display_name, callable_) in DOCUMENTED_API.items()
    }


def test_api_signatures_come_from_runtime_defaults() -> None:
    plot = format_api_signature(".plot", DOCUMENTED_API["plot"][1])
    images = format_api_signature(".images", DOCUMENTED_API["images"][1])

    assert "fun=None" in plot
    assert "paths=None" in images


def test_meta_includes_package_version(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "meta.typ"
    monkeypatch.setattr("docs.build_examples.BUILD", tmp_path)
    monkeypatch.setattr("docs.build_examples.__version__", "1.2.3")

    write_meta()

    assert '#let version = "1.2.3"' in output.read_text(encoding="utf-8")


def test_color_reference_uses_the_bundled_color_values(tmp_path: Path) -> None:
    output = tmp_path / "colors.typ"

    write_color_reference(output)

    rendered = output.read_text(encoding="utf-8")
    assert 'box(fill: rgb("#808080")' in rendered
    assert "text(fill: black)[gray]" in rendered
    assert 'box(fill: rgb("#000080")' in rendered
    assert "text(fill: white)[navy]" in rendered
