"""Plot/image directive execution. guide 09."""

from __future__ import annotations

import base64
import inspect
import pathlib
import shutil
import tempfile
from collections.abc import Callable
from typing import TYPE_CHECKING

from ._indices import resolve_i, resolve_j
from ._utils import _new_image_id, format_markup_num

if TYPE_CHECKING:
    from ._tinytable import TinyTable

try:
    import matplotlib

    matplotlib.use("Agg")
except ImportError:
    pass


def _require_images() -> None:
    try:
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401
    except ImportError as e:
        raise ImportError(
            ".plot()/.images() require the 'images' extra:\n"
            "    pip install tinytables[images]"
        ) from e


def _height_to_float(h: str | float) -> float:
    if isinstance(h, str):
        return float(h.replace("em", "").strip())
    return float(h)


def _accepts_kwargs(fun: Callable) -> bool:
    try:
        sig = inspect.signature(fun)
        return "color" in sig.parameters or any(
            p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
        )
    except (ValueError, TypeError):
        return False


def _save_plot_image(fun: Callable, entry: object, path: str | pathlib.Path, *, width_px: int, height_px: int, color: str, xlim: object) -> None:
    import matplotlib.pyplot as plt

    obj = fun(entry, color=color, xlim=xlim) if _accepts_kwargs(fun) else fun(entry)

    if hasattr(obj, "save") and not isinstance(obj, plt.Figure):
        obj.save(
            filename=str(path),
            width=width_px / 100,
            height=height_px / 100,
            dpi=100,
            verbose=False,
        )
    elif isinstance(obj, plt.Figure):
        obj.savefig(str(path), dpi=100, transparent=True, bbox_inches="tight", pad_inches=0)
        plt.close(obj)
    else:
        raise TypeError(
            f".plot() fun must return a matplotlib Figure or a plotnine ggplot; "
            f"got {type(obj).__name__}"
        )


def _make_svg_wrapper(png_bytes: bytes, width_px: int, height_px: int) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width_px}' height='{height_px}' "
        f"viewBox='0 0 {width_px} {height_px}'>"
        f"<image href='data:image/png;base64,{b64}' width='{width_px}' height='{height_px}' "
        f"preserveAspectRatio='xMidYMid meet'/>"
        f"</svg>"
    )


def _escape_typst_bytes(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


def _build_image_cell_string(
    relpath: str, height: float, output: str, portable: bool, png_path: str | None, width_px: int, height_px: int
) -> str:
    h = format_markup_num(height)
    if output == "typst":
        if portable and png_path is not None:
            with open(png_path, "rb") as f:
                png_bytes = f.read()
            svg = _make_svg_wrapper(png_bytes, width_px, height_px)
            escaped = _escape_typst_bytes(svg)
            return f'#image(bytes("{escaped}"), format: "svg", height: {h}em)'
        else:
            path = relpath.replace("\\", "/")
            return f'#image("{path}", height: {h}em)'
    elif output == "html":
        path = relpath.replace("\\", "/")
        return f'<img src="{path}" style="height: {h}em;">'
    else:
        return "[plot]"


def execute_plots(
    table: TinyTable,
    data_body: list[list[str]],
    typed_body: list[list[object]],
    output: str,
    *,
    nhead: int,
    has_header: bool,
    n_merged_body: int,
    group_positions: set[int],
) -> None:
    if not table._plot_directives:
        return

    _require_images()

    portable = table._typst_opts.portable
    colnames = table._colnames

    temp_dirs: list[str] = []

    for rank, d in enumerate(table._plot_directives):
        if d.output is not None and output not in d.output:
            continue

        i_vals = resolve_i(
            d.i,
            nhead=nhead,
            group_positions=group_positions,
            n_merged_body=n_merged_body,
            has_header=has_header,
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
        j_vals = resolve_j(d.j, colnames)

        height = _height_to_float(d.height)

        for ri, i in enumerate(body_rows):
            body_row = i - 1
            if body_row < 0 or body_row >= len(data_body):
                continue

            for rj, j in enumerate(j_vals):
                col_idx = j - 1
                if col_idx < 0 or col_idx >= len(data_body[body_row]):
                    continue

                if d.images is not None:
                    total_idx = ri * len(j_vals) + rj
                    if total_idx < len(d.images):
                        img_path = d.images[total_idx].replace("\\", "/")
                        cell_str = _build_image_cell_string(
                            img_path, height, output, portable, None, d.width_px, d.height_px
                        )
                        data_body[body_row][col_idx] = cell_str
                else:
                    if d.data is not None:
                        total_idx = ri * len(j_vals) + rj
                        entry = d.data[total_idx]
                    else:
                        entry = typed_body[body_row][col_idx]

                    if portable:
                        td = tempfile.mkdtemp(prefix="tinytables_portable_")
                        temp_dirs.append(td)
                        assets_dir = pathlib.Path(td)
                    else:
                        assets_dir = table._assets_dir
                        if assets_dir is None:
                            assets_dir = pathlib.Path.cwd() / "tinytable_assets"
                        assets_dir = pathlib.Path(assets_dir)

                    assets_dir.mkdir(parents=True, exist_ok=True)

                    image_id = _new_image_id()
                    name = "plot"
                    filename = f"{name}_{rank:04d}_{image_id}.png"
                    png_path = assets_dir / filename

                    _save_plot_image(
                        d.fun,
                        entry,
                        png_path,
                        width_px=d.width_px,
                        height_px=d.height_px,
                        color=d.color,
                        xlim=d.xlim,
                    )

                    if portable:
                        relpath = filename
                    else:
                        assets_relpath = table._assets_relpath
                        if assets_relpath:
                            relpath = f"{assets_relpath}/{filename}"
                        else:
                            relpath = f"tinytable_assets/{filename}"

                    cell_str = _build_image_cell_string(
                        relpath,
                        height,
                        output,
                        portable,
                        str(png_path),
                        d.width_px,
                        d.height_px,
                    )
                    data_body[body_row][col_idx] = cell_str

    for td in temp_dirs:
        shutil.rmtree(td, ignore_errors=True)
