# Typst compilation benchmark

`typst_compile.py` generates three reports and times fresh `typst compile` processes. Python rendering, formatting callbacks, and image generation happen before timing. Each default report has 15 different tables of 30 data rows and 20 columns, one table per A4 landscape page.

- `plain`: text labels and numeric columns with the default appearance.
- `styled`: euro formatting, striped backgrounds, a styled header, conditional text colors, bold cells, indentation, and custom padding.
- `sparklines`: the same styling with 450 distinct embedded SVG sparklines, one per data row. These SVGs are deliberately simple; complex matplotlib SVGs or other report content can change the balance of compilation costs.

Run this before changing the renderer to retain baseline Typst sources, then run it again after the change:

```sh
uv run python benchmarks/typst_compile.py --output-dir build/perf-before
uv run python benchmarks/typst_compile.py --output-dir build/perf-after --compare build/perf-before --repeat 9
```

Use identical table dimensions for both runs. The comparison recompiles both sets of sources, alternating order after an initial warmup. Reported values are medians of fresh CLI processes with warm filesystem/font caches. They measure complete PDF compilation and export, including process startup; they do not measure incremental recompilation in watch mode. The sources, PDFs, and individual samples in `results.json` remain in the output directories. Add `--timings` to save a Typst trace for each source in an additional compilation outside the timed samples.

On Linux x86_64 (Intel Core i5-9500T) with Typst 0.15.0, nine-run medians for the renderer change from style lookups to native cell properties were:

| Report | Before | After | Less time |
| --- | ---: | ---: | ---: |
| Plain | 0.461 s | 0.329 s | 29% |
| Styled | 0.664 s | 0.440 s | 34% |
| Styled with SVG sparklines | 0.661 s | 0.468 s | 29% |

An accompanying styled-report trace reduced `func call` events from 262,621 to 16,505. Native table cells still require padding and layout, so eliminating style callbacks removes only part of the compilation work. These are local measurements of synthetic reports, not a guaranteed speedup for other documents. The benchmark is kept outside the test suite to avoid a machine-dependent compilation-time gate.

The renderer retains scoped whole-cell transforms for rotation, and for font sizing or indentation when the surrounding document supplies the table inset. Identical transforms are coalesced into contiguous row selections. Vertical-only alignment uses an indexed alignment grid to retain the surrounding document's horizontal alignment. These compatibility paths avoid assuming that an included table has Typst's default inset or outer alignment.
