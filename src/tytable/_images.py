"""Execute static-image and generated-plot directives at render time."""

from __future__ import annotations

import base64
import hashlib
import inspect
import pathlib
import re
import tempfile
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast

from ._directives import ImageDirective
from ._indices import resolve_i
from ._utils import format_markup_num

if TYPE_CHECKING:
    from ._tytable import TyTable

StaticImagePolicy: TypeAlias = Literal["copy", "reference", "embed"]


@dataclass(frozen=True)
class MediaContext:
    """Invocation-local static-image policy and optional external-media destination."""

    static_images: StaticImagePolicy = "reference"
    assets_dir: pathlib.Path | None = None
    assets_relpath: str | None = None
    source_dir: pathlib.Path = field(default_factory=pathlib.Path.cwd)


def validate_static_image_policy(value: str) -> StaticImagePolicy:
    """Validate and narrow a public static-image policy value."""
    if value not in ("copy", "reference", "embed"):
        raise ValueError(f"static_images must be 'copy', 'reference', or 'embed'; got {value!r}")
    return cast(StaticImagePolicy, value)


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


def _image_format(data: bytes) -> tuple[str, str] | None:
    """Return the Typst format and MIME type for supported embedded image bytes."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif", "image/gif"
    prefix = data[:2048].lstrip(b"\xef\xbb\xbf\x00\t\n\r ").lower()
    if prefix.startswith(b"<svg") or (prefix.startswith(b"<?xml") and b"<svg" in prefix):
        return "svg", "image/svg+xml"
    return None


def _typst_embedded_bytes(data: bytes) -> str:
    """Encode arbitrary bytes as a Typst byte-array expression."""
    values = ", ".join(str(value) for value in data)
    return f"bytes(({values}))"


def _static_image_bytes(
    raw_path: str,
    media_context: MediaContext,
    *,
    context: str,
) -> tuple[pathlib.Path, bytes]:
    """Resolve and read one local static image with contextual failures."""
    parsed = urllib.parse.urlsplit(raw_path)
    windows_drive = bool(re.match(r"^[A-Za-z]:[\\/]", raw_path))
    if parsed.scheme and not windows_drive:
        raise ValueError(
            f"{context}: static_images={media_context.static_images!r} requires a local file; "
            f"got {raw_path!r}"
        )
    path = pathlib.Path(raw_path)
    if not path.is_absolute():
        path = media_context.source_dir / path
    try:
        return path, path.read_bytes()
    except OSError as e:
        raise OSError(f"{context}: could not read static image {str(path)!r}: {e}") from e


def _static_asset_name(path: pathlib.Path, digest: str) -> str:
    """Return a readable, filesystem-safe, content-addressed asset name."""
    stem = (re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("._-") or "image")[:80]
    suffix = path.suffix.lower()
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,10}", suffix):
        suffix = ""
    return f"image_{stem}_{digest}{suffix}"


def _write_static_asset(
    source: pathlib.Path,
    data: bytes,
    media_context: MediaContext,
    cache: dict[str, str],
    *,
    context: str,
) -> str:
    """Copy one static image into the invocation's asset directory, with deduplication."""
    assets_dir = media_context.assets_dir
    assets_relpath = media_context.assets_relpath
    if assets_dir is None or assets_relpath is None:
        raise ValueError("static_images='copy' requires .save() with an output location")
    digest = hashlib.sha256(data).hexdigest()
    filename = cache.get(digest)
    if filename is None:
        filename = _static_asset_name(source, digest)
        cache[digest] = filename
        try:
            assets_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(
                f"{context}: could not create asset directory {str(assets_dir)!r}: {e}"
            ) from e
        destination = assets_dir / filename
        try:
            destination.write_bytes(data)
        except OSError as e:
            raise OSError(
                f"{context}: could not write static image asset {str(destination)!r}: {e}"
            ) from e
    return f"{assets_relpath.rstrip('/')}/{filename}"


def _build_image_cell_string(
    relpath: str,
    height: float,
    output: str,
    embed: bool,
    image_data: bytes | None,
    image_format: tuple[str, str] | None = None,
    width_px: int = 0,
    height_px: int = 0,
) -> str:
    """Build the markup string for one image cell, backend- and portability-specific."""
    h = format_markup_num(height)
    if output == "typst":
        if embed and image_data is not None:
            if image_format is None:
                svg = _make_svg_wrapper(image_data, width_px, height_px)
                escaped = _escape_typst_bytes(svg)
                return f'#image(bytes("{escaped}"), format: "svg", height: {h}em)'
            typst_format, _mime = image_format
            encoded = _typst_embedded_bytes(image_data)
            return f'#image({encoded}, format: "{typst_format}", height: {h}em)'
        else:
            return f'#image("{_escape_typst_bytes(relpath)}", height: {h}em)'
    elif output == "html":
        from html import escape

        if embed and image_data is not None:
            mime = "image/png" if image_format is None else image_format[1]
            encoded = base64.b64encode(image_data).decode("ascii")
            return f'<img src="data:{mime};base64,{encoded}" style="height: {h}em;">'
        return f'<img src="{escape(relpath, quote=True)}" style="height: {h}em;">'
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
    static_context = media_context if media_context is not None else MediaContext()
    static_asset_cache: dict[str, str] = {}

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
            cell_context = (
                f"{'.images()' if isinstance(d, ImageDirective) else '.plot()'} directive "
                f"{rank + 1}, selected cell (row={body_row}, column={col_idx})"
            )
            if isinstance(d, ImageDirective):
                img_path = d.images[total_idx]
                if output == "ascii":
                    cell_str = "[image]"
                elif static_context.static_images == "reference":
                    cell_str = _build_image_cell_string(img_path, height, output, False, None)
                else:
                    source, image_data = _static_image_bytes(
                        img_path, static_context, context=cell_context
                    )
                    if static_context.static_images == "copy":
                        relpath = _write_static_asset(
                            source,
                            image_data,
                            static_context,
                            static_asset_cache,
                            context=cell_context,
                        )
                        cell_str = _build_image_cell_string(relpath, height, output, False, None)
                    else:
                        image_format = _image_format(image_data)
                        if image_format is None:
                            raise ValueError(
                                f"{cell_context}: cannot embed unsupported static image format "
                                f"from {img_path!r} in {output} output"
                            )
                        cell_str = _build_image_cell_string(
                            "",
                            height,
                            output,
                            True,
                            image_data,
                            image_format,
                        )
                data_body[body_row][col_idx] = cell_str
                image_cells.add((body_row, col_idx))
            else:
                entry = d.data[total_idx] if d.data is not None else typed_body[body_row][col_idx]

                if output == "ascii":
                    cell_str = "[plot]"
                elif media_context is None or media_context.assets_dir is None:
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
                            context=cell_context,
                        )
                        png_bytes = png_path.read_bytes()
                    cell_str = _build_image_cell_string(
                        "",
                        height,
                        output,
                        True,
                        png_bytes,
                        None,
                        d.width_px,
                        d.height_px,
                    )
                else:
                    assets_dir = media_context.assets_dir
                    assets_relpath = media_context.assets_relpath
                    if assets_relpath is None:
                        raise ValueError("saved generated plots require an asset reference path")
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
                    relpath = f"{assets_relpath.rstrip('/')}/{filename}"
                    cell_str = _build_image_cell_string(
                        relpath,
                        height,
                        output,
                        False,
                        None,
                        None,
                        d.width_px,
                        d.height_px,
                    )
                data_body[body_row][col_idx] = cell_str
                image_cells.add((body_row, col_idx))

    return image_cells
