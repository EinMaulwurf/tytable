"""
Run every example script in ``examples/`` to regenerate ``build/*.typ``.

Each ``NN_*.py`` file is a self-contained, runnable example that saves its
Typst output under ``build/``.  ``main.typ`` then ``#read``\ s the source for
display and ``#include``\ s the generated table for rendering, so the example
file is the single source of truth.

Also writes ``build/meta.typ`` (git short hash + build date) for the title-page
version stamp consumed by ``main.typ``.

Run:  uv run python docs/build_examples.py
"""

import datetime
import os
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
BUILD = ROOT / "build"


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
    (BUILD / "meta.typ").write_text(f'#let commit = "{commit}"\n#let build_date = "{build_date}"\n')


def main() -> None:
    os.chdir(ROOT)
    scripts = sorted(EXAMPLES.glob("[0-9][0-9]_*.py"))
    if not scripts:
        print("no example scripts found", file=sys.stderr)
        raise SystemExit(1)
    for script in scripts:
        print(f"running {script.relative_to(ROOT)} ...")
        runpy.run_path(str(script), run_name="__main__")
    write_meta()
    print(f"done: {len(scripts)} examples built")


if __name__ == "__main__":
    main()
