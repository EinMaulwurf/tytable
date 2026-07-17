"""Execute static-image and generated-plot directives at render time."""

from __future__ import annotations

import base64
import hashlib
import inspect
import pathlib
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ._directives import ImageDirective
from ._indices import resolve_i
from ._utils import format_markup_num

if TYPE_CHECKING:
    from ._tytable import TyTable


@dataclass(frozen=True)
class MediaContext:
    """Invocation-local destination and reference prefix for generated plots."""

    assets_dir: pathlib.Path
    assets_relpath: str


def _require_plotting() -> None:
    """Raise an informative ``ImportError`` if Matplotlib is not installed."""
    try:
        import matplotlib
    except ImportError as e:
        raise ImportError(
            ".plot() requires the 'images' extra:\n    pip install tytable[images]"
        ) from e
    if matplotlib.get_backend() == "module://matplotlib_inline.backend_inline":
        matplotlib.use("Agg")


def _height_to_float(h: str | float) -> float:
    """Coerce a height spec (number or ``"1.5em"``) to a plain float."""
    if isinstance(h, str):
        return float(h.replace("em", "").strip())
    return float(h)


def _callback_kwargs(fun: Callable, *, color: str, xlim: object) -> dict[str, object]:
    """Return only the optional plot keywords that ``fun`` can accept."""
    try:
        sig = inspect.signature(fun)
    except (ValueError, TypeError):
        return {}

    parameters = sig.parameters
    if any(p.kind == p.VAR_KEYWORD for p in parameters.values()):
        return {"color": color, "xlim": xlim}

    keyword_kinds = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    available = {name for name, parameter in parameters.items() if parameter.kind in keyword_kinds}
    values: dict[str, object] = {"color": color, "xlim": xlim}
    return {name: value for name, value in values.items() if name in available}


def _save_plot_image(
    fun: Callable,
    entry: object,
    path: str | pathlib.Path,
    *,
    width_px: int,
    height_px: int,
    color: str,
    xlim: object,
    context: str,
) -> None:
    """Call ``fun(entry)``, then save the returned Figure/ggplot to ``path`` as a PNG."""
    import matplotlib.pyplot as plt

    dpi = 100
    try:
        obj = fun(entry, **_callback_kwargs(fun, color=color, xlim=xlim))
    except Exception as e:
        raise RuntimeError(f"{context}: plot callback failed: {e}") from e

    try:
        if hasattr(obj, "save") and not isinstance(obj, plt.Figure):
            obj.save(
                filename=str(path),
                width=width_px / dpi,
                height=height_px / dpi,
                dpi=dpi,
                verbose=False,
            )
        elif isinstance(obj, plt.Figure):
            obj.set_size_inches(width_px / dpi, height_px / dpi, forward=True)
            obj.savefig(
                str(path),
                dpi=dpi,
                transparent=True,
                bbox_inches=obj.bbox_inches,
                pad_inches=0,
            )
        else:
            raise TypeError(
                f"{context}: fun must return a matplotlib Figure or a plotnine ggplot; "
                f"got {type(obj).__name__}"
            )
    except OSError as e:
        raise OSError(f"{context}: could not write plot asset {str(path)!r}: {e}") from e
    finally:
        if isinstance(obj, plt.Figure):
            plt.close(obj)


def _make_svg_wrapper(png_bytes: bytes, width_px: int, height_px: int) -> str:
    """Wrap PNG bytes in a minimal inline SVG (used for portable Typst images)."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width_px}' height='{height_px}' "
        f"viewBox='0 0 {width_px} {height_px}'>"
        f"<image href='data:image/png;base64,{b64}' width='{width_px}' height='{height_px}' "
        f"preserveAspectRatio='xMidYMid meet'/>"
        f"</svg>"
    )


def _escape_typst_bytes(s: str) -> str:
    """Escape backslashes and double-quotes for embedding inside a Typst string literal."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


def _build_image_cell_string(
    relpath: str,
    height: float,
    output: str,
    embed: bool,
    png_path: str | None,
    width_px: int = 0,
    height_px: int = 0,
) -> str:
    """Build the markup string for one image cell, backend- and portability-specific."""
    h = format_markup_num(height)
    if output == "typst":
        if embed and png_path is not None:
            with open(png_path, "rb") as f:
                png_bytes = f.read()
            svg = _make_svg_wrapper(png_bytes, width_px, height_px)
            escaped = _escape_typst_bytes(svg)
            return f'#image(bytes("{escaped}"), format: "svg", height: {h}em)'
        else:
            path = relpath.replace("\\", "/")
            return f'#image("{_escape_typst_bytes(path)}", height: {h}em)'
    elif output == "html":
        from html import escape

        if embed and png_path is not None:
            with open(png_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("ascii")
            return f'<img src="data:image/png;base64,{encoded}" style="height: {h}em;">'
        path = relpath.replace("\\", "/")
        return f'<img src="{escape(path, quote=True)}" style="height: {h}em;">'
    else:
        return "[plot]"


def execute_plots(
    table: TyTable,
    data_body: list[list[str]],
    typed_body: list[list[Any]],
    output: str,
    *,
    media_context: MediaContext | None,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
) -> set[tuple[int, int]]:
    """Run generated-plot and static-image directives, writing image markup in place.

    Returns the set of ``(row, col)`` positions where safe image markup was injected,
    so callers can selectively skip HTML/Typst escaping for those cells.
    """
    image_cells: set[tuple[int, int]] = set()
    if not table._media_directives:
        return image_cells

    for rank, d in enumerate(table._media_directives):
        if d.output is not None and output not in d.output:
            continue

        i_vals = resolve_i(
            d.i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
            data=table._data,
        )
        if i_vals is None:
            i_vals = resolve_i(
                "body",
                nhead=nhead,
                group_positions=group_positions,
                n_merged_body=n_merged_body,
                has_header=has_header,
            )
        if i_vals is None:
            i_vals = []

        body_rows = [i for i in i_vals if i > 0]
        j_vals = table._resolve_j(d.j, regex=d.regex)

        target_cells = [
            (i - 1, j - 1)
            for i in body_rows
            for j in j_vals
            if i <= len(data_body) and j <= len(data_body[i - 1])
        ]
        supplied = d.images if isinstance(d, ImageDirective) else d.data
        if supplied is not None and len(supplied) != len(target_cells):
            argument = "paths" if isinstance(d, ImageDirective) else "data"
            method = ".images()" if isinstance(d, ImageDirective) else ".plot()"
            raise ValueError(
                f"{method} {argument} has {len(supplied)} item(s), but the resolved "
                f"selection contains {len(target_cells)} cell(s)"
            )

        if not isinstance(d, ImageDirective) and output != "ascii":
            try:
                _require_plotting()
            except ImportError as e:
                raise ImportError(f".plot() directive {rank + 1}: {e}") from e

        height = _height_to_float(d.height)

        for total_idx, (body_row, col_idx) in enumerate(target_cells):
            if isinstance(d, ImageDirective):
                img_path = d.images[total_idx].replace("\\", "/")
                cell_str = _build_image_cell_string(img_path, height, output, False, None)
                data_body[body_row][col_idx] = cell_str
                image_cells.add((body_row, col_idx))
            else:
                entry = d.data[total_idx] if d.data is not None else typed_body[body_row][col_idx]

                if output == "ascii":
                    cell_str = "[plot]"
                elif media_context is None:
                    with tempfile.TemporaryDirectory(prefix="tytable_portable_") as td:
                        png_path = pathlib.Path(td) / f"plot_{rank:04d}_{total_idx:04d}.png"
                        _save_plot_image(
                            d.fun,
                            entry,
                            png_path,
                            width_px=d.width_px,
                            height_px=d.height_px,
                            color=d.color,
                            xlim=d.xlim,
                            context=(
                                f".plot() directive {rank + 1}, selected cell "
                                f"(row={body_row}, column={col_idx})"
                            ),
                        )
                        cell_str = _build_image_cell_string(
                            "",
                            height,
                            output,
                            True,
                            str(png_path),
                            d.width_px,
                            d.height_px,
                        )
                else:
                    assets_dir = media_context.assets_dir
                    try:
                        assets_dir.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        raise OSError(
                            f".plot() directive {rank + 1}: could not create asset directory "
                            f"{str(assets_dir)!r}: {e}"
                        ) from e
                    with tempfile.TemporaryDirectory(prefix="tytable_plot_") as td:
                        temporary = pathlib.Path(td) / "plot.png"
                        _save_plot_image(
                            d.fun,
                            entry,
                            temporary,
                            width_px=d.width_px,
                            height_px=d.height_px,
                            color=d.color,
                            xlim=d.xlim,
                            context=(
                                f".plot() directive {rank + 1}, selected cell "
                                f"(row={body_row}, column={col_idx})"
                            ),
                        )
                        png_bytes = temporary.read_bytes()
                    digest = hashlib.sha256(png_bytes).hexdigest()[:12]
                    filename = f"plot_{rank:04d}_{total_idx:04d}_{digest}.png"
                    png_path = assets_dir / filename
                    try:
                        png_path.write_bytes(png_bytes)
                    except OSError as e:
                        raise OSError(
                            f".plot() directive {rank + 1}: could not write plot asset "
                            f"{str(png_path)!r}: {e}"
                        ) from e
                    relpath = f"{media_context.assets_relpath.rstrip('/')}/{filename}"
                    cell_str = _build_image_cell_string(
                        relpath,
                        height,
                        output,
                        False,
                        str(png_path),
                        d.width_px,
                        d.height_px,
                    )
                data_body[body_row][col_idx] = cell_str
                image_cells.add((body_row, col_idx))

    return image_cells
