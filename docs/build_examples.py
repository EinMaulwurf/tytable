r"""
Run every example script in ``examples/`` to regenerate ``build/*.typ``.

Each ``NN_*.py`` file is a self-contained, runnable example that saves its
Typst output under ``build/``.  ``main.typ`` then ``#read``\ s the source for
display and ``#include``\ s the generated table for rendering, so the example
file is the single source of truth.

Also writes ``build/meta.typ`` (git short hash + build date) for the title-page
version stamp and ``build/api.json`` with signatures derived from the public
Python callables consumed by ``main.typ``.

Run:  uv run python docs/build_examples.py
"""

import datetime
import inspect
import json
import os
import runpy
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tytable import TyTable, __version__, tt

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
BUILD = ROOT / "build"

DOCUMENTED_API: dict[str, tuple[str, Callable[..., Any]]] = {
    "tt": ("tt", tt),
    "style": (".style", TyTable.style),
    "fmt": (".fmt", TyTable.fmt),
    "group": (".group", TyTable.group),
    "set_name": (".set_name", TyTable.set_name),
    "theme": (".theme", TyTable.theme),
    "theme_striped": (".theme_striped", TyTable.theme_striped),
    "theme_grid": (".theme_grid", TyTable.theme_grid),
    "theme_empty": (".theme_empty", TyTable.theme_empty),
    "theme_rotate": (".theme_rotate", TyTable.theme_rotate),
    "theme_resize": (".theme_resize", TyTable.theme_resize),
    "plot": (".plot", TyTable.plot),
    "images": (".images", TyTable.images),
    "finalize": (".finalize", TyTable.finalize),
    "render": (".render", TyTable.render),
    "save": (".save", TyTable.save),
}


def _return_annotation(annotation: Any) -> str:
    if annotation is inspect.Signature.empty:
        return ""
    if isinstance(annotation, str):
        return annotation
    if annotation is None:
        return "None"
    return getattr(annotation, "__name__", str(annotation))


def _parameter_tokens(signature: inspect.Signature) -> list[str]:
    parameters = [
        parameter for parameter in signature.parameters.values() if parameter.name != "self"
    ]
    tokens: list[str] = []
    inserted_kw_marker = False
    positional_only = [
        parameter for parameter in parameters if parameter.kind is inspect.Parameter.POSITIONAL_ONLY
    ]

    for parameter in parameters:
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY and not inserted_kw_marker:
            if not any(item.kind is inspect.Parameter.VAR_POSITIONAL for item in parameters):
                tokens.append("*")
            inserted_kw_marker = True
        tokens.append(str(parameter.replace(annotation=inspect.Parameter.empty)))
        if positional_only and parameter is positional_only[-1]:
            tokens.append("/")
    return tokens


def format_api_signature(display_name: str, callable_: Callable[..., Any]) -> str:
    """Format a callable's real parameters as a compact documentation signature."""
    signature = inspect.signature(callable_)
    tokens = _parameter_tokens(signature)
    return_annotation = _return_annotation(signature.return_annotation)
    suffix = f" -> {return_annotation}" if return_annotation else ""
    one_line = f"{display_name}({', '.join(tokens)}){suffix}"
    if len(one_line) <= 88:
        return one_line

    lines: list[str] = []
    current = "    "
    for token in tokens:
        addition = f"{token},"
        separator = " " if current.strip() else ""
        if len(current) + len(separator) + len(addition) > 88 and current.strip():
            lines.append(current)
            current = f"    {addition}"
        else:
            current += separator + addition
    if current.strip():
        lines.append(current)
    return f"{display_name}(\n" + "\n".join(lines) + f"\n){suffix}"


def write_api_signatures(path: Path = BUILD / "api.json") -> None:
    signatures = {
        key: format_api_signature(display_name, callable_)
        for key, (display_name, callable_) in DOCUMENTED_API.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(signatures, indent=2) + "\n")


def write_meta() -> None:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    build_date = datetime.date.today().isoformat()
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "meta.typ").write_text(
        f'#let version = "{__version__}"\n'
        f'#let commit = "{commit}"\n'
        f'#let build_date = "{build_date}"\n'
    )


def main() -> None:
    os.chdir(ROOT)
    scripts = sorted(EXAMPLES.glob("[0-9][0-9]_*.py"))
    if not scripts:
        print("no example scripts found", file=sys.stderr)
        raise SystemExit(1)
    for script in scripts:
        print(f"running {script.relative_to(ROOT)} ...")
        runpy.run_path(str(script), run_name="__main__")
    write_api_signatures()
    write_meta()
    print(f"done: {len(scripts)} examples built")


if __name__ == "__main__":
    main()
