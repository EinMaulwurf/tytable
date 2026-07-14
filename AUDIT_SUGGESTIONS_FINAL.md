# Audit Suggestions — Final

> **Usage**: Tell your coding agent to start at the first unchecked item and mark it `[x]` when verified. Items are ordered by priority within each tier.

Generated 2026-07-13 from two independent audits (6-dimension subagent audit + manual deep-dive audit). Merged and de-duplicated. 48 code/tooling items + 10 testing items = 58 total.

---

## CRITICAL (fix before public release)

- [x] **C-1** — [files: `LICENSE`, `pyproject.toml`] Fix LICENSE vs pyproject.toml mismatch.

  LICENSE file is GPL-3.0 (with unfilled template placeholders). pyproject.toml declares `license = "MIT"`. This is legally contradictory. Decide on one license and align both files.

- [x] **C-2** — [src/tytable/_format.py:118-124] Fix falsy `or` fallback that silently applies format directives to wrong rows.

  ```python
  # Current (bug): empty list `[]` is falsy, triggers fallback to "body"
  i_vals = resolve_i(d.i, ...) or resolve_i("body", ...)

  # Fix: distinguish None (unresolved) from [] (resolved to no rows)
  i_vals = resolve_i(d.i, ...)
  if i_vals is None:
      i_vals = resolve_i("body", ...)
  ```

- [x] **C-3** — [src/tytable/_resolve.py:229-231] Fix HTML `<img` escape bypass.

  `if not val.startswith("<img")` skips HTML escaping for ANY cell starting with `<img`, not just library-generated image cells. A crafted value `<img src=x onerror=alert(1)>` renders as raw HTML. Replace with a `set[tuple[int,int]]` of image-cell coordinates populated by `execute_plots()` and check membership instead.

- [x] **C-4** — [src/tytable/_colors.py:185] Fix Typst code injection via style property values.

  `color_to_typst()` passes unrecognized color strings through unchanged. A value like `'red); #pagebreak(); //'` injects arbitrary Typst commands. Validate against a whitelist (hex, named colors, known functions) and reject values containing `\n`, `;`, `(`, `)`.

- [x] **C-5** — [src/tytable/_tytable.py:22, src/tytable/_resolve.py:19] Eliminate 310ms import-time matplotlib penalty.

  `matplotlib.use("Agg")` at `_images.py:20` is reached via `_tytable.py → _resolve.py → _images.py` at import time. Move `from ._resolve import build` inside the `render()` method, and `from ._images import execute_plots` inside the `build()` function. Also guard `matplotlib.use("Agg")` with a `matplotlib.get_backend()` check to avoid overriding user-set backends.

- [x] **C-6** — [src/tytable/_resolve.py:173-177, src/tytable/_render_html.py:211] Fix HTML column-name double-escaping.

  `build()` applies `escape_html()` to column names, then `HtmlRenderer` applies it again. Result: `X&amp;lt;Y` instead of `X&lt;Y`. Either skip the pre-escape for HTML output in `_resolve.py` or add a flag to `BuiltTable.colnames_display` indicating "already escaped."

- [x] **C-7** — [src/tytable/_render_html.py:84,86] Add CSS injection protection for style property values.

  `color` and `background` values are interpolated directly into CSS `style` attributes. `.style(color='red;"><script>alert(1)</script>')` injects script tags. Sanitize the values — reject characters `"`, `'`, `;`, `(`, `)`, `<`, `>`, `\`, newlines.

---

## HIGH

- [x] **H-1** — [src/tytable/_escape.py:7-23] Add missing backtick and tilde to Typst escape set.

  `` ` `` (code span delimiter) and `~` (non-breaking space) are Typst metacharacters but not in `TYPST_ESCAPE`. Add ``"`"`` and `"~"` to the dict and regex.

- [x] **H-2** — [src/tytable/_format.py:129-132] Fix `fmt(i="header")` silently dropped.

  Format directives targeting header rows are silently skipped because `data_body` only contains data rows. Emit a warning when `i` resolves to header indices and a format directive cannot apply. Optionally support formatting column names (at least `replace` and `fn`).

- [x] **H-3** — [src/tytable/_render_typst.py:107] Fix truthiness bug: `align_figure or "l"`.

  `self.align_figure or "l"` silently replaces empty string `""` with `"l"`. Use `"l" if self.align_figure is None else self.align_figure`.

- [x] **H-4** — [src/tytable/_escape.py:35-36,44-45] Make escape functions type-safe.

  `escape_typst` and `escape_html` are typed `str -> str` but silently return non-string values (bool, int, None) for non-string inputs. Convert eagerly (`return str(text)`) or raise `TypeError`.

- [x] **H-5** — [src/tytable/_tytable.py:763-774] Add clear error for `set_name` with non-string name.

  `set_name(j="a", name=123)` raises `TypeError: 'int' object is not iterable`. Add explicit `isinstance(name, str)` check with a clear error message before falling through to list coercion.

- [x] **H-6** — [src/tytable/_format.py:125] Replace bare `assert` with explicit runtime check.

  `assert i_vals is not None` is stripped under `python -O`. Replace with:

  ```python
  if i_vals is None:
      raise RuntimeError("i_vals unexpectedly None in apply_formats")
  ```

- [x] **H-7** — [src/tytable/_tytable.py:177-179] Fix frozen `Note` mutation via `object.__setattr__`.

  `_assign_markers` bypasses `frozen=True` using `object.__setattr__`. Either make `Note` non-frozen, or replace in-list with new instances via `dataclasses.replace()`.

- [x] **H-8** — [src/tytable/_tytable.py:260-264] Parameterize internal list type annotations.

  Bare `list` annotations defeat type narrowing. Import the directive types and parameterize:

  ```python
  self._style_directives: list[StyleDirective] = []
  self._format_directives: list[FormatDirective] = []
  self._plot_directives: list[PlotDirective] = []
  self._row_groups: list[RowGroup] = []
  ```

- [x] **H-9** — [src/tytable/_resolve.py:197-198] Fix `build()` mutation of TinyTable state (render idempotency).

  `build()` mutates `table._nhead` and `table._n_merged_body_rows`. This makes repeated `render()` calls stateful. Make them local variables or return them in `BuiltTable` instead.

- [x] **H-10** — [src/tytable/_images.py:128-131] Fix XSS via unescaped image path in HTML `src` attribute.

  In `_build_image_cell_string()`, call `escape_html()` on the image path before interpolating into `<img src="...">`.

- [x] **H-11** — [src/tytable/_images.py:126-128] Fix Typst injection via unescaped image path.

  In `_build_image_cell_string()`, escape `"` and `\` in the path before interpolating into `#image("...")` string literal.

- [x] **H-12** — [src/tytable/_render_typst.py:37-40] Add Typst escape/sanitization to `_props_to_signature()` as defense-in-depth.

  After fixing C-4 (color injection), add explicit rejection of property values containing `#`, `(`, `)`, `;`, `[`, `]` as a second layer of defense.

- [x] **H-13** — [src/tytable/_tytable.py:193] Fix `bool` silently treated as scalar width.

  `isinstance(width, (int, float, str))` matches `True`/`False` since `bool` is a subclass of `int`. `_normalize_width(True, 3)` returns `True` (treated as scalar 1). Add `if isinstance(width, bool): raise TypeError(...)` before the check.

---

## MEDIUM

- [ ] **M-3** — [src/tytable/__init__.py] Document `THEMES` constant.

  `THEMES` is exported in `__all__` but has zero documentation. Users don't know it's a `dict[str, Callable]`. Add docstring and a section in the user guide.

- [ ] **M-4** — [src/tytable/_tytable.py] Add `Raises:` sections to all 12 public method docstrings.

  0/12 public methods document their exceptions. Add `Raises: ValueError: ...` for invalid selectors, invalid style properties, missing required args, etc.

- [ ] **M-5** — [src/tytable/_tytable.py] Widen `j` type annotations to accept `list[str]`.

  `j` is annotated as `int | str | Sequence[int | str] | None` but the runtime in `_indices.py` already handles `list[str]`. The annotation gap causes false type-checker errors.

- [ ] **M-6** — [src/tytable/_tytable.py:854-859] Define a `Renderer` ABC and replace hardcoded dispatch.

  Create a `class Renderer(ABC)` with `render(built: BuiltTable) -> str`. Make `TypstRenderer`, `HtmlRenderer`, `AsciiRenderer` inherit from it. Use a registry dict instead of if/elif dispatch.

- [ ] **M-7** — [src/tytable/_render_html.py, src/tytable/_render_ascii.py] Remove unused `_opts` ghost parameter.

  `HtmlRenderer.render()` and `AsciiRenderer.render()` accept `_opts` but never use it. Drop the parameter.

- [ ] **M-8** — [src/tytable/_render_typst.py, src/tytable/_render_html.py] Extract shared col-group span logic.

  The col-group row rendering in `_render_typst.py:430-455` and `_render_html.py:167-197` is ~70% identical. Extract a shared utility `_resolve_col_group_spans(cg_row) -> list[tuple[str, int, int]]`.

- [ ] **M-9** — [src/tytable/_render_typst.py, src/tytable/_render_html.py, src/tytable/_format.py, src/tytable/_styling.py] Split large methods with McCabe > 15.

  `HtmlRenderer.render()` (CC 45), `TypstRenderer.render()` (CC 29), `apply_formats()` (CC 30), `_validate_style()` (CC 26). Extract `_emit_header()`, `_emit_body()`, `_emit_styles()` helpers. Convert `_validate_style` to a declarative schema loop.

- [ ] **M-10** — [src/tytable/_render_typst.py, src/tytable/_render_html.py] Consolidate duplicated style-to-markup translation.

  `_props_to_signature()`, `_style_typst_content()`, `_build_cell_style()`, `_style_html_inline()` translate the same ~15 properties into four different markup formats. Extract shared logic into an intermediate representation or translator class.

- [ ] **M-11** — [src/tytable/_resolve.py:143-294] Break up `build()` god function.

  Extract sub-functions: `_extract_body()`, `_merge_groups()`, `_run_prepare_hooks()`, `_reorder_directives()`, `_apply_formatting()`, `_apply_global_escape()`, `_execute_plots()`, `_insert_footnotes()`, `_build_style_grid()`, `_apply_meta_styles()`, `_apply_colspans()`.

- [x] **M-12** — [src/tytable/_images.py:211-259] Replace `tempfile.mkdtemp` with `TemporaryDirectory` context manager.

  `shutil.rmtree(td, ignore_errors=True)` is best-effort cleanup; temp dirs leak on unhandled exceptions. Use `tempfile.TemporaryDirectory()` as a context manager.

- [x] **M-13** — [src/tytable/_themes.py:94] Add validation for `theme_typst(**opts)` kwargs.

  After setting attributes, validate that all keys are in `dataclasses.fields(TypstRenderOptions)`. Raise `ValueError` with valid keys for any unknown option.

- [x] **M-14** — [src/tytable/_resolve.py:200-211] Fix prepare-hooks fragile reordering.

  Themes add directives during `build()`, and the code reorders by snapshotting lengths before/after. If a hook does anything other than append, order corrupts silently. Add a dedicated `_deferred_style()` method on `TinyTable` so themes register intent explicitly.

- [ ] **M-15** — [src/tytable/_directives.py] Separate `PlotDirective` into `PlotDirective` and `ImageDirective`.

  One dataclass serves `.plot()` (has `fun`/`data`/`xlim`) and `.images()` (has `images`). These are disjoint operations. Create separate types.

- [ ] **M-16** — [src/tytable/_tytable.py:844, src/tytable/_resolve.py:150] Use `Literal["typst", "html", "ascii"]` for `output` parameter.

  Currently typed as `str`. `Literal` gives IDE autocompletion and catches typos at type-check time.

- [ ] **M-17** — [src/tytable/_render_html.py:206,240, src/tytable/_format.py:85-87] Move lazy imports to module top level.

  `from ._indices import convert_row_to_typst` appears inside `render()` twice. `from ._escape import escape_html` is inside a loop body. Move all to top-level imports.

- [x] **M-18** — [src/tytable/_styling.py:176-185] Precompute active props in `build_style_grid`.

  Inner loop calls `getattr(d, prop)` for 15 props per cell × per directive = ~55K calls for a 120×30 table. Most directives set only 1-2 props. Precompute:

  ```python
  active_props = {p: v for p in OVERWRITE_PROPS if (v := getattr(d, p)) is not None}
  ```

- [ ] **M-19** — [src/tytable/_render_typst.py:22-52, src/tytable/_colors.py:159, src/tytable/_escape.py:33] Add `@lru_cache` to hot-path pure functions.

  `_props_to_signature` called 3,630 times for 6 unique prop-sets. `color_to_typst` called 3,720 times for 5 unique colors. `escape_typst` called 3,630 times on numeric strings. Cache all three. Estimated savings: ~8ms on 120×30, ~260ms on 500×100.

- [ ] **M-20** — [src/tytable/_themes.py] Add error context to theme application.

  In `_apply_theme()`, wrap the theme callable invocation in try/except and re-raise with the theme name in the error message.

- [x] **M-21** — [src/tytable/_indices.py:198-206] Add ReDoS protection for user-controlled regex patterns.

  Add a length limit on regex patterns (e.g., 500 chars). For Python ≥3.11, pass a timeout to `re.compile`. Consider `regex` library for older Python versions.

- [ ] **M-22** — [src/tytable/_groups.py:86,93] Handle `None` values in row-group label generation.

  `label=str(prev)` where `prev` may be `None` produces the string `"None"`. Use `str(prev) if prev is not None else "NA"` or skip `None` values.

- [ ] **M-23** — [src/tytable/_styling.py:160, src/tytable/_format.py:118] Document or align default row selectors.

  `.style(i=None)` defaults to `"all"`. `.fmt(i=None)` defaults to `"body"`. Either make them consistent or document the difference prominently in both docstrings.

- [ ] **M-24** — [src/tytable/_styling.py:242-260] Skip `compute_covered_cells()` when no spans present.

  The function iterates the entire style grid every render. Most tables have zero colspan/rowspan. Track during `build_style_grid()` whether any spans were set; skip completely if not.

- [ ] **M-25** — [src/tytable/_resolve.py:158-170] Merge double inner loop into single pass.

  `data_body` (strings) and `typed_body` (raw values) are built in two separate loops iterating the same cells. Combine into one pass.

- [ ] **M-26** — [src/tytable/_themes.py] Make `theme_resize` warn on non-Typst outputs.

  `theme_resize` sets `_typst_opts` which only the Typst renderer reads. HTML/ASCII outputs silently ignore it. Raise a warning.

- [ ] **M-27** — [src/tytable/_images.py:211-259] Add explicit image-cell tracking for escaping.

  Have `execute_plots()` populate a `set` of `(row, col)` positions where safe image markup was injected. Use this set in the escaping loop instead of the `startswith("<img")` prefix check (C-3).

- [ ] **M-28** — [pyproject.toml] Add upper bound on polars dependency.

  Change `"polars>=1.0"` to `"polars>=1.0,<2"` to prevent breaking changes on major version bumps.

---

## LOW

- [ ] **L-1** — [src/tytable/_styling.py, src/tytable/_themes.py] Extract magic numbers to `_constants.py`.

  Define `DEFAULT_LINE_WIDTH = 0.1`, `THEME_TOP_BOTTOM_RULE = 0.08`, `THEME_HEADER_RULE = 0.05`, etc. Replace hardcoded values throughout.

- [ ] **L-2** — [README.md] Add badges, extras documentation, and Python version requirement.

  No CI/Python-version/license badges. No mention of `tytable[images]` extra. No Python version requirement listed.

- [ ] **L-3** — [pyproject.toml] Add per-version Python classifiers.

  CI tests 3.10–3.13 but only generic `Programming Language :: Python :: 3` classifier exists. Add classifiers for each version.

- [ ] **L-4** — [pyproject.toml] Fix `authors` field.

  Currently `{ name = "tytable" }` — the author name is the project name. Use an actual name or GitHub handle.

- [ ] **L-5** — [docs/main.typ, docs/examples/] Add missing user guide examples.

  Missing: `rotate` theme, `regex=True`, `.finalize()`, `output=` directive filtering, caption/notes styling (no rendered output), `.images()` standalone, escape on/off contrast, troubleshooting section.

- [ ] **L-6** — [docs/] Add Sphinx-based API reference.

  Documentation is a beautiful Typst PDF but no searchable, cross-referenced HTML API reference. Add minimal Sphinx setup (`sphinx.ext.autodoc` + `sphinx.ext.napoleon`) to generate from existing docstrings.

- [ ] **L-7** — [tests/test_perf.py] Tighten performance gate and expand coverage.

  Current gate: 0.3s for 120×30 that renders in <20ms (15× headroom). Tighten to 0.08s. Add HTML rendering, `fmt()` with digits, per-cell styling, and a 500×100 stress test (2s budget).

- [ ] **L-8** — [tests/] Add test coverage for `__init__.py` version fallback.

  `__version__` fallback paths (hatch-vcs vs. `importlib.metadata.version` vs. `"0.0.0"`) have 45% coverage. Patch `_version.py` import to verify each path.

- [ ] **L-9** — [src/tytable/_images.py:45-53] Fix `_accepts_kwargs` silent swallow.

  Built-in/C extensions that don't support `inspect.signature` silently return `False`, causing `color`/`xlim` to never be passed even if the function supports `**kwargs`. Log a warning or try-call with fallback.

- [ ] **L-10** — [src/tytable/_tytable.py:769-771] Fix `set_name` duplicate-column first-match surprise.

  `set_name` allows duplicate names but `j` selectors use `colnames.index(x)` which only matches the first. Either match all duplicates or raise on duplicate introduction.

- [ ] **L-11** — [src/tytable/_groups.py:26] Fix `from None` suppressing debug context.

  `raise ValueError(...) from None` hides the `list.index()` traceback. Use `from e` or omit.

- [ ] **L-12** — [src/tytable/_tytable.py:207-209] Fix width double-normalization.

  Width normalization happens in two places (dividing by sum in `_tytable.py`, multiplying by 100 in `_render_typst.py`). Normalize in one place only.

- [ ] **L-13** — [src/tytable/_styling.py:72-89] Guard `_expand_align()` calls.

  Called for every directive even when `align`/`alignv` is `None`. Add `if d.align is not None` and `if d.alignv is not None` guards.

- [ ] **L-14** — [src/tytable/_tytable.py] Split monolithic `_tytable.py` (908 lines).

  Move render dispatch and file I/O to a new `_render.py` module. Keep directive recording in `_tytable.py`.

- [ ] **L-15** — [src/tytable/_tytable.py] Remove or implement `rownames` dead parameter.

  `rownames` is documented as "Reserved — not yet implemented." Either implement it or remove the parameter to avoid confusion.

- [ ] **L-16** — [src/tytable/_render_typst.py, src/tytable/_render_html.py] Add docstrings to `TypstRenderer` and `HtmlRenderer` classes.

  Module docstrings exist but the classes themselves lack docstrings.

- [ ] **L-17** — [src/tytable/_images.py] Expand module docstring.

  Current: `"Plot/image directive execution. guide 09."` — expand to cover both directive types and the portable-vs-filesystem rendering paths.

- [ ] **L-18** — [src/tytable/_utils.py:13-21] Skip `is_integer()` check for obviously-fractional floats.

  Every float cell calls `float.is_integer()`. Most values are non-integer; skip the check when `abs(v - int(v)) > 1e-12`.

- [ ] **L-19** — [.gitignore] Fix `TODO.md` in `.gitignore` conflict.

  `.gitignore` lists `TODO.md` but the file is tracked. Either remove from `.gitignore` or rename the tracked file to `ROADMAP.md`.

- [ ] **L-20** — [CI] Add security scanning to CI.

  Add a GitHub Actions workflow running `bandit -r src/ -ll` and `pip-audit`.

---

## TESTING

- [x] **T-1** — [tests/] Add tests for empty DataFrame rendering (0 rows).

  Create a `pl.DataFrame()` with columns but 0 rows, render with all three backends, assert no crash.

- [x] **T-2** — [tests/] Add tests for `rowspan` styling parameter.

  Test `rowspan` renders correctly in Typst and HTML. Test `compute_covered_cells()` with rowspan > 1.

- [x] **T-3** — [tests/] Add unit tests for `color_to_typst()`.

  Test: named colors, 3/4/6/8-digit hex, "black"/"white", empty string, invalid hex, unknown strings (should raise ValueError after C-4).

- [x] **T-4** — [tests/] Add unit tests for `format_markup_num()`.

  Test: ints, floats (whole-number vs fractional), bools, None, complex types.

- [x] **T-5** — [tests/] Add unit tests for `_matches()`, `_apply_replace()`, `_apply_escape()`.

  Currently only tested through full render pipeline. Add direct unit tests for each formatting utility.

- [x] **T-6** — [tests/] Add unit tests for `compute_covered_cells()`.

  Test colspan and rowspan coverage logic with various configurations.

- [x] **T-7** — [tests/] Add Unicode/emoji rendering tests.

  Test that Japanese, emoji, RTL text, and combining marks survive all three render pipelines without corruption.

- [x] **T-8** — [tests/] Add tests for `save()` with plain Typst/HTML output (no images).

  Test `table.save("output.typ")` and `table.save("output.html")` write correct files.

- [x] **T-9** — [tests/] Add test for row grouping with list input (run-length encoding).

  `register_row_groups` accepts a list form — verify it produces correct group separators.

- [x] **T-10** — [tests/] Add test for `build()` raising `NotImplementedError` on unknown output format.

  Simple `pytest.raises(NotImplementedError, match=...)`.

---

## DEFERRED (need more data before committing)

- [ ] **D-1** — Consider removing `set_name()` per-column mode. `colnames_override` at construction covers the 95% case. Defer until user feedback clarifies demand.

- [ ] **D-2** — Consider collapsing `tt()` 12 kwargs into grouped config objects. Would add boilerplate for simple cases. Defer until parameter count grows further.

- [ ] **D-3** — Consider dropping `num_fmt="significant"`. Defer until usage data is available.

- [ ] **D-4** — Consider eliminating the internal 1-based row index convention. Would cut `_indices.py` by ~100 lines but requires touching ~20 call sites. Defer until after other refactors stabilize.

- [ ] **D-5** — Consider splitting `replace` into `na_fill` + `substitute` parameters. Clearer semantics but a breaking change. Defer until a major version bump.

---

**Totals**: 7 CRITICAL + 13 HIGH + 28 MEDIUM + 20 LOW + 10 TESTING + 5 DEFERRED = 83 items
