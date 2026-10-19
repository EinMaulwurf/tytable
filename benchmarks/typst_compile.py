"""Measure fresh Typst-to-PDF processes, excluding Python table generation.

Run before and after a renderer change using separate output directories::

    uv run python benchmarks/typst_compile.py --output-dir build/perf-before
    uv run python benchmarks/typst_compile.py --output-dir build/perf-after \
        --compare build/perf-before

Each report contains 15 different 30-by-20 tables, one per landscape page.
The SVG case uses small, distinct embedded sparklines (no matplotlib required).
Comparison runs alternate order to reduce bias. Timings are medians of fresh
CLI processes with warm filesystem caches, not incremental watch-mode builds.
Use --timings to also save a Typst trace, outside the measured runs.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import subprocess
import time
from pathlib import Path

import polars as pl

from tytable import tt
from tytable.formatters import currency


def generate_reports(directory: Path, tables: int, rows: int, columns: int) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    preamble = '#set page(paper: "a4", flipped: true, margin: 10mm)\n#set text(size: 6pt)\n'
    reports: dict[str, list[str]] = {name: [] for name in ("plain", "styled", "sparklines")}
    for index in range(tables):
        numeric = [f"Q{col}" for col in range(1, columns)]
        df = pl.DataFrame(
            {"Item": [f"Account {index * rows + row}" for row in range(rows)]}
            | {
                name: [
                    ((row * 73 + col * 19 + index * 31) % 2000 - 500) / 10 for row in range(rows)
                ]
                for col, name in enumerate(numeric)
            }
        )
        base = tt(df, figure=False, width=1)
        reports["plain"].append(base.render("typst"))
        styled = base.clone().theme_striped().fmt(j=numeric, fn=currency("EUR", locale="de_DE"))
        styled.style(i="header", bold=True, color="white", background="#334155", padding=0.5)
        styled.style(j="Item", indent=0.5)
        for col, name in enumerate(numeric):
            styled.style(j=name, i=pl.col(name) < 0, color="#b91c1c")
            styled.style(j=name, i=[row for row in range(rows) if (row + col) % 7 == 0], bold=True)
        reports["styled"].append(styled.render("typst"))
        paths = []
        for row in range(rows):
            rng = random.Random(index * rows + row)
            points = " ".join(f"{x * 6},{rng.randrange(2, 18)}" for x in range(12))
            path = directory / f"spark-{index}-{row}.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="68" height="20">'
                f'<polyline points="{points}" fill="none" stroke="#2563eb"/></svg>',
                encoding="utf-8",
            )
            paths.append(str(path.resolve()))
        reports["sparklines"].append(
            styled.clone()
            .images(j=numeric[-1], paths=paths, height=1)
            .render("typst", static_images="embed")
        )
    for name, fragments in reports.items():
        (directory / f"{name}.typ").write_text(
            preamble + "\n#pagebreak()\n".join(fragments), encoding="utf-8"
        )


def compile_report(source: Path, *, timings: bool = False) -> float:
    command = ["typst", "compile", str(source), str(source.with_suffix(".pdf"))]
    if timings:
        command += ["--timings", str(source.with_suffix(".json"))]
    start = time.perf_counter()
    subprocess.run(command, capture_output=True, text=True, check=True)
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--tables", type=int, default=15)
    parser.add_argument("--rows", type=int, default=30)
    parser.add_argument("--columns", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--timings", action="store_true")
    args = parser.parse_args()
    if min(args.tables, args.rows, args.repeat) < 1 or args.columns < 2:
        parser.error("tables, rows, repeat must be positive; columns must be at least 2")
    generate_reports(args.output_dir, args.tables, args.rows, args.columns)
    results = {}
    print(subprocess.check_output(["typst", "--version"], text=True).strip(), flush=True)
    for name in ("plain", "styled", "sparklines"):
        sources = {"current": args.output_dir / f"{name}.typ"}
        if args.compare:
            sources["baseline"] = args.compare / f"{name}.typ"
        for source in sources.values():
            compile_report(source)  # Warm filesystem and font caches.
        samples: dict[str, list[float]] = {key: [] for key in sources}
        for run in range(args.repeat):
            keys = list(sources) if run % 2 == 0 else list(reversed(sources))
            for key in keys:
                samples[key].append(compile_report(sources[key]))
        medians = {key: statistics.median(values) for key, values in samples.items()}
        results[name] = {"seconds": samples, "median_seconds": medians}
        message = f"{name}: {medians['current']:.3f}s"
        if args.compare:
            message += f" (baseline {medians['baseline']:.3f}s, {medians['baseline'] / medians['current']:.2f}x)"
        print(message, flush=True)
        if args.timings:
            for source in sources.values():
                compile_report(source, timings=True)
    (args.output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
