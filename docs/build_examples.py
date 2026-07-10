"""Run every example script in ``examples/`` to regenerate ``build/*.typ``.

Each ``NN_*.py`` file is a self-contained, runnable example that saves its
Typst output under ``build/``.  ``main.typ`` then ``#read``\\ s the source for
display and ``#include``\\ s the generated table for rendering, so the example
file is the single source of truth.

Run:  uv run python docs/build_examples.py
"""

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"


def main() -> None:
    os.chdir(ROOT)
    scripts = sorted(EXAMPLES.glob("[0-9][0-9]_*.py"))
    if not scripts:
        print("no example scripts found", file=sys.stderr)
        raise SystemExit(1)
    for script in scripts:
        print(f"running {script.relative_to(ROOT)} ...")
        runpy.run_path(str(script), run_name="__main__")
    print(f"done: {len(scripts)} examples built")


if __name__ == "__main__":
    main()
