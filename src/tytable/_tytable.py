"""
Public API: the ``tt()`` factory and the :class:`TinyTable` class.

All styling, formatting, grouping, and plotting is recorded as *intent* and
replayed in a fixed order when ``.render()`` / ``.save()`` is called.
"""

from __future__ import annotations

import pathlib
import re
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any, TypeAlias

import polars as pl

from ._directives import FormatDirective, Note, PlotDirective, RowGroup, StyleDirective
from ._groups import register_col_groups, register_row_groups
from ._indices import resolve_j
from ._render_ascii import AsciiRenderer
from ._render_html import HtmlRenderer
from ._render_typst import TypstRenderer, TypstRenderOptions
from ._renderer import Renderer
from ._styling import _validate_style
from ._themes import THEMES

_ColumnSelector: TypeAlias = int | str | Sequence[int] | Sequence[str] | None


def tt(
    data: pl.DataFrame,
    *,
    figure: bool = True,
    caption: str | None = None,
    label: str | None = None,
    notes: list | None = None,
    width: float | Sequence[float | str | None] | str | None = None,
    height: float | None = None,
    gutter: float | str | None = 2,
    colnames: bool = True,
    colnames_override: dict[str, str] | None = None,
    rownames: bool = False,
    digits: int | None = None,
    escape: bool = True,
    theme: str | Callable | None = "default",
    finalize: Callable[[str, str], str] | None = None,
) -> TinyTable:
    """
    Create a :class:`TinyTable` from a Polars DataFrame.

    This is the main entry point of the library. The returned table is
    configured by chaining methods — ``.style()``, ``.fmt()``, ``.group()``,
    ``.theme()``, ``.plot()`` — and finally rendered to Typst, HTML, or ASCII
    with ``.render()`` or ``.save()``. All chaining methods return the table
    (``self``), so a single fluent expression can describe a complex table.

    Parameters
    ----------
    data
        The Polars DataFrame to render. The frame is cloned, so the original
        is never mutated.
    figure
        Wrap Typst output in a ``figure`` (default ``True``). Set ``False``
        to emit an unnumbered table without figure semantics. Captions and
        labels require ``figure=True``.
    caption
        Table caption (rendered as a Typst ``figure`` caption or an HTML
        ``<caption>``). ``None`` omits it.
    label
        Typst label attached to the figure, without angle brackets, for
        cross-references such as ``@product-scores``. Requires
        ``figure=True``. Ignored by non-Typst renderers.
    notes
        List of footnotes. Each entry may be a plain ``str`` (untargeted note),
        a :class:`dict` with keys ``text``, ``marker``, ``i``, ``j``, or a
        :class:`~tytable._directives.Note`. Notes attached to cells via ``i`` /
        ``j`` get auto-numbered superscript markers.
    width
        Column-width spec. A float fraction (``1`` = full width, ``0.5`` =
        half), a per-column list of fractions/strings/``None`` (``None`` =
        auto), or a Typst/HTML length string such as ``"3.5cm"``. ``None`` lets
        every column auto-size. A per-column list must have one entry per
        column; when every entry is numeric and the list sums to more than 1,
        each entry is divided by the sum so the table fills the available width
        with relative column sizes.
    height
        Row height in ``em`` (Typst). ``None`` = auto rows.
    gutter
        Typst column gutter. A number is treated as points; a string such as
        ``"0.1em"`` is passed through. ``None`` suppresses the gutter.
    colnames
        Show the column-name header row (default ``True``).
    colnames_override
        Mapping ``{original_name: display_name}`` renaming columns for display
        only (the dataframe itself is untouched).
    rownames
        Reserved — not yet implemented; kept for API parity with R tinytable.
    digits
        Global default number of decimal places applied to every numeric
        column. Per-column overrides are set with ``.fmt(digits=...)``.
    escape
        Escape cell text for the target backend (default ``True``). Typst and
        HTML metacharacters are escaped automatically; set ``False`` to pass
        raw markup through.
    theme
        Built-in theme name (``"default"``, ``"striped"``, ``"grid"``,
        ``"empty"``, ``"rotate"``), a callable ``theme(table) -> TinyTable``,
        or ``None`` for no theme.
    finalize
        Optional post-render callback ``fn(rendered_string, output) -> str``
        run after every renderer; equivalent to calling ``.finalize(fn)``.

    Returns
    -------
    TinyTable
        A new table ready for further chaining.

    Raises
    ------
    TypeError
        If ``width`` or one of its entries has an unsupported type.
    ValueError
        If figure metadata, ``width``, or the requested theme is invalid.

    Examples
    --------
    >>> import polars as pl
    >>> from tytable import tt
    >>> df = pl.DataFrame({"x": [1, 2], "y": [3.5, 4.5]})
    >>> type(tt(df))
    <class 'tytable._tytable.TinyTable'>

    A minimal table written to disk:

    >>> tt(df, caption="demo").save("build/demo.typ")  # doctest: +SKIP

    Chain formatting and styling before the terminal ``.save()``:

    >>> (tt(df, width=1)                     # doctest: +SKIP
    ...  .fmt(j="y", digits=2)
    ...  .style(i="header", bold=True)
    ...  .save("build/demo.typ"))
    """

    t = TinyTable(
        data,
        figure=figure,
        caption=caption,
        label=label,
        notes=notes,
        width=width,
        height=height,
        gutter=gutter,
        colnames=colnames,
        colnames_override=colnames_override,
        rownames=rownames,
        digits=digits,
        escape=escape,
        theme=theme,
    )
    if finalize is not None:
        t.finalize(finalize)
    return t


def _normalize_notes(raw: list[Any]) -> list[Note]:
    """Coerce a heterogeneous ``notes`` list into ``Note`` dataclass instances."""
    if not raw:
        return []
    result = []
    for item in raw:
        if isinstance(item, Note):
            result.append(item)
        elif isinstance(item, dict):
            result.append(
                Note(
                    text=item.get("text", ""),
                    marker=item.get("marker"),
                    i=item.get("i"),
                    j=item.get("j"),
                )
            )
        elif isinstance(item, str):
            result.append(Note(text=item))
        else:
            result.append(Note(text=str(item)))
    return _assign_markers(result)


def _assign_markers(notes: list[Note]) -> list[Note]:
    """Auto-number targeted notes (those with ``i``/``j``) in document order."""
    auto = 0
    result: list[Note] = []
    for note in notes:
        if note.marker is not None:
            result.append(note)
            continue
        if note.i is not None or note.j is not None:
            auto += 1
            result.append(replace(note, marker=str(auto)))
        else:
            result.append(note)
    return result


_TYPST_LABEL_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.:-]*$")


def _validate_figure_options(figure: bool, caption: str | None, label: str | None) -> None:
    """Validate figure-only metadata and keep label interpolation safe."""
    if not figure and (caption is not None or label is not None):
        raise ValueError("caption and label require figure=True")
    if label is not None and not _TYPST_LABEL_RE.fullmatch(label):
        raise ValueError(
            "label must contain only letters, numbers, underscores, hyphens, periods, or colons"
        )


def _normalize_width(
    width: float | Sequence[float | str | None] | str | None, ncol: int
) -> float | Sequence[float | str | None] | str | None:
    """Validate and normalize the ``width`` spec.

    A per-column list must have one entry per column; each numeric entry must be
    non-negative. When every entry is numeric and the list sums to more than 1,
    each entry is divided by the sum so the table fills the available width with
    relative column sizes (mirrors the tinytable contract). Mixed lists
    (containing ``None`` or length strings) are left untouched.
    """
    if isinstance(width, bool):
        raise TypeError("width must be a number, string, sequence, or None; bool is not supported")
    if width is None or isinstance(width, (int, float, str)):
        return width
    entries = list(width)
    if len(entries) != ncol:
        raise ValueError(f"width list must have one entry per column ({ncol}), got {len(entries)}")
    nums = []
    for w in entries:
        if w is None or isinstance(w, str):
            continue
        if isinstance(w, bool) or not isinstance(w, (int, float)):
            raise ValueError(f"width entries must be a number, string, or None, got {w!r}")
        if w < 0:
            raise ValueError(f"width entries must be non-negative, got {w!r}")
        nums.append(w)
    if len(nums) == len(entries) and sum(nums) > 1:
        total = sum(nums)
        return [n / total for n in nums]
    return entries


class TinyTable:
    """
    A chainable table built from a Polars DataFrame.

    Instances are normally created with the :func:`tt` factory rather than
    constructed directly. The class records styling, formatting, grouping, and
    plotting as *intent*; nothing is rendered until ``.render()`` or
    ``.save()`` is called, so row indices always refer to the final, visible
    table.

    Every mutator method (``.style()``, ``.fmt()``, ``.group()``, ``.theme()``,
    ``.plot()``, ``.images()``, ``.finalize()``) returns ``self`` to enable
    fluent chaining. ``.render()`` and ``.save()`` are terminal.
    """

    def __init__(
        self,
        data: pl.DataFrame,
        *,
        figure: bool = True,
        caption: str | None = None,
        label: str | None = None,
        notes: list | None = None,
        width: float | Sequence[float | str | None] | str | None = None,
        height: float | None = None,
        gutter: float | str | None = 2,
        colnames: bool = True,
        colnames_override: dict[str, str] | None = None,
        rownames: bool = False,
        digits: int | None = None,
        escape: bool = True,
        theme: str | Callable | None = "default",
    ) -> None:
        """Direct constructor — prefer the :func:`tt` factory.

        See :func:`tt` for parameter documentation.

        Raises
        ------
        TypeError
            If ``width`` or one of its entries has an unsupported type.
        ValueError
            If figure metadata, ``width``, or the requested theme is invalid.
        """
        _validate_figure_options(figure, caption, label)
        self._data = data.clone()
        self._colnames: list[str] = (
            [colnames_override.get(c, c) for c in data.columns]
            if colnames_override
            else list(data.columns)
        )
        self._show_colnames = colnames
        self._caption = caption
        self._label = label
        self._width = _normalize_width(width, data.width)
        self._height = height
        self._escape = escape
        self._rownames = rownames
        self._digits = digits
        self._theme_name = theme

        self._style_directives: list[StyleDirective] = []
        self._deferred_style_directives: list[StyleDirective] = []
        self._format_directives: list[FormatDirective] = []
        self._plot_directives: list[PlotDirective] = []
        self._row_groups: list[RowGroup] = []
        self._col_group_rows: list[list[str | None]] = []
        self._notes: list[Note] = _normalize_notes(notes or [])
        self._prepare_hooks: list[Callable[[TinyTable], None]] = []
        self._finalize_hooks: list[Callable[[str, str], str]] = []
        self._nhead: int = 0
        self._n_merged_body_rows: int = 0
        self._assets_dir: str | None = None
        self._assets_relpath: str | None = None

        self._typst_opts = TypstRenderOptions(figure=figure, multipage=False)
        if height is not None:
            self._typst_opts.row_height_em = float(height)
        self._typst_opts.column_gutter = gutter

        self._apply_theme(theme)

    def _apply_theme(self, theme: str | Callable | None) -> None:
        """Resolve a theme spec (name, callable, or ``None``) and apply it to the table."""
        if theme is None:
            return
        if callable(theme):
            theme(self)
            return
        if isinstance(theme, str):
            fn = THEMES.get(theme)
            if fn is None:
                raise ValueError(f"Unknown theme: {theme!r}. Available: {list(THEMES)}")
            fn(self)
            return

    def style(
        self,
        i: int
        | str
        | Sequence[int | str]
        | pl.Expr
        | pl.Series
        | Callable[[dict], bool]
        | None = None,
        j: _ColumnSelector = None,
        *,
        regex: bool = False,
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        strikeout: bool | None = None,
        monospace: bool | None = None,
        smallcaps: bool | None = None,
        color: str | None = None,
        background: str | None = None,
        fontsize: float | None = None,
        align: str | None = None,
        alignv: str | None = None,
        indent: float | None = None,
        colspan: int | None = None,
        rowspan: int | None = None,
        rotate: float | None = None,
        line: str | None = None,
        line_color: str | None = None,
        line_width: float | None = 0.1,
        line_trim: str | None = None,
        output: tuple[str, ...] | None = None,
    ) -> TinyTable:
        """
        Apply per-cell styling via row/column selectors.

        Parameters
        ----------
        i
            Row selector: ``0`` = first data row, ``"header"`` = column-name
            row, negative ints = column-group header rows (``-1`` topmost),
            ``"groupi"`` / ``"groupj"`` = row/column group separators, or a
            ``list[int]``. ``None`` means *all* rows.
        j
            Column selector: a name (``"Score"``), an integer position (``0``),
            or a ``list`` of any of these. ``None`` means *all* columns.
            Set ``regex=True`` to interpret string selectors as regular
            expression patterns matched against column names via
            :func:`re.search`.
        regex
            When ``True``, string ``j`` selectors (including elements of a
            list) are treated as :func:`re.search` patterns instead of exact
            column names.
        bold, italic, underline, strikeout, monospace, smallcaps
            Boolean text decorations.
        color
            Foreground text color (hex, named, or Typst expression).
        background
            Cell background color.
        fontsize
            Font size in ``em``.
        align
            Horizontal alignment: ``"l"`` / ``"c"`` / ``"r"``. When ``j``
            selects multiple columns, a multi-char string like ``"llr"``
            sets per-column alignment (one char per selected column).
        alignv
            Vertical alignment: ``"t"`` / ``"m"`` / ``"b"``. Per-column
            strings (e.g. ``"tmb"``) are supported like ``align``.
        indent
            Left indent in ``em``.
        colspan, rowspan
            Merge the selected cell across ``N`` columns/rows.
        rotate
            Rotation angle in degrees for the cell content (e.g. ``90``
            rotates text vertically). Useful for long column headers on
            narrow data columns. Typst uses ``#rotate(…, reflow: true)``;
            HTML uses ``transform:rotate(…)``. Ignored by the ASCII renderer.
        line
            Per-side border, any combination of ``t`` (top), ``b`` (bottom),
            ``l`` (left), ``r`` (right) — e.g. ``"tblr"`` or ``"b"``.
        line_color
            Border color (default ``"black"``).
        line_width
            Border width in ``em`` (default ``0.1``).
        line_trim
            Optional Typst ``table.hline``/``vline`` trim spec.
        output
            Restrict this directive to the given output backends
            (e.g. ``("typst",)``). ``None`` applies to all.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        TypeError
            If a color or numeric style property has an unsupported type.
        ValueError
            If a style property is invalid. Invalid row or column selectors
            raise when the table is rendered.

        Notes
        -----
        Any number of properties may be combined in a single call when they
        share the same ``i``/``j`` selector — one directive, not several. Value
        formatting such as ``digits`` lives in :meth:`fmt`, a separate pipeline,
        and so always needs its own call.

        Examples
        --------
        >>> df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        >>> (tt(df)                           # doctest: +SKIP
        ...  .style(i="header", bold=True, background="#2c3e50", color="white")
        ...  .style(j="b", align="r", background="#f0f0f0")
        ...  .style(i=0, line="b", line_color="#bdc3c7"))
        """
        _validate_style(
            align=align,
            alignv=alignv,
            line=line,
            color=color,
            background=background,
            line_color=line_color,
            colspan=colspan,
            rowspan=rowspan,
            line_width=line_width,
            fontsize=fontsize,
            indent=indent,
            rotate=rotate,
        )
        self._style_directives.append(
            StyleDirective(
                i=i,
                j=j,
                regex=regex,
                bold=bold,
                italic=italic,
                underline=underline,
                strikeout=strikeout,
                monospace=monospace,
                smallcaps=smallcaps,
                color=color,
                background=background,
                fontsize=fontsize,
                align=align,
                alignv=alignv,
                indent=indent,
                colspan=colspan,
                rowspan=rowspan,
                rotate=rotate,
                line=line,
                line_color=line_color,
                line_width=line_width,
                line_trim=line_trim,
                output=output,
            )
        )
        return self

    def _deferred_style(self, *args: Any, **kwargs: Any) -> TinyTable:
        """Record a prepare-hook style separately so user styles retain precedence."""
        before = len(self._style_directives)
        self.style(*args, **kwargs)
        if len(self._style_directives) != before + 1:
            raise RuntimeError("style() did not record exactly one directive")
        self._deferred_style_directives.append(self._style_directives.pop())
        return self

    def fmt(
        self,
        i: int
        | str
        | Sequence[int | str]
        | pl.Expr
        | pl.Series
        | Callable[[dict], bool]
        | None = None,
        j: _ColumnSelector = None,
        *,
        regex: bool = False,
        digits: int | None = None,
        num_fmt: str = "decimal",
        replace: dict | str | bool | None = None,
        escape: bool = False,
        fn: Callable | None = None,
        output: tuple[str, ...] | None = None,
    ) -> TinyTable:
        """
        Apply value formatting to selected cells.

        ``digits``, ``replace``, ``escape``, and ``fn`` may be combined in a
        single call — they run in that order.

        Parameters
        ----------
        i, j
            Row/column selectors — see :meth:`style`. ``i`` defaults to *all
            body rows*, ``j`` to *all columns*.
        digits
            Number of decimal places. Combined with ``num_fmt``.
        num_fmt
            Numeric style: ``"decimal"`` (fixed decimals, default) or
            ``"significant"`` (significant figures).
        replace
            Substitute values: ``True`` blanks out nulls/NaNs, a ``str`` fills
            them, or a ``{old: new}`` dict maps old (typed values or string
            matches, including ``"null"``, ``"nan"``, ``"inf"``) to new.
        escape
            Re-escape cell text for the target backend after other transforms.
        fn
            Custom column-wise transform ``fn(values: list[str]) -> list[str]``.
            Called once per selected column with the current string values; the
            returned list must have the same length.
        output
            Restrict this directive to the given output backends. ``None``
            applies to all.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        TypeError
            If a row or column selector has an unsupported type; raised when
            the table is rendered.
        ValueError
            If a selector is invalid or ``fn`` returns the wrong number of
            values; raised when the table is rendered.

        Examples
        --------
        >>> df = pl.DataFrame({"rev": [12450.5, None]})
        >>> (tt(df)                                # doctest: +SKIP
        ...  .fmt(j="rev", digits=2)
        ...  .fmt(j="rev", replace={"null": "—"}))
        """
        self._format_directives.append(
            FormatDirective(
                i=i,
                j=j,
                regex=regex,
                digits=digits,
                num_fmt=num_fmt,
                replace=replace,
                escape=escape,
                fn=fn,
                output=output,
            )
        )
        return self

    def plot(
        self,
        i: int
        | str
        | Sequence[int | str]
        | pl.Expr
        | pl.Series
        | Callable[[dict], bool]
        | None = None,
        j: _ColumnSelector = None,
        *,
        regex: bool = False,
        fun: Callable | None = None,
        data: list | None = None,
        height: float | str = 1.0,
        height_px: int = 400,
        width_px: int = 1200,
        color: str = "black",
        xlim: list[float] | None = None,
        output: tuple[str, ...] | None = None,
    ) -> TinyTable:
        """
        Embed a generated plot in each selected cell.

        Requires the ``images`` extra (``pip install tytable[images]``).

        Parameters
        ----------
        i, j
            Row/column selectors — see :meth:`style`. ``j`` is required. ``i``
            defaults to *all body rows*.
        fun
            Plotting callable. Called once per selected row with either the
            typed cell value (or the ``data`` list entry) plus optional
            ``color`` / ``xlim`` keyword arguments. Must return a matplotlib
            ``Figure`` or a plotnine ``ggplot``.
        data
            Optional per-cell data overriding the cell's own value. Indexed
            row-major across the selected cells.
        height
            Plot height in ``em`` (default ``1.0``).
        height_px, width_px
            Pixel dimensions of the generated PNG (default 400×1200).
        color
            Color forwarded to ``fun`` (default ``"black"``).
        xlim
            Optional x-axis limits forwarded to ``fun``.
        output
            Restrict this directive to the given output backends. ``None``
            applies to all.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        ValueError
            If ``j`` or ``fun`` is missing, ``height`` cannot be parsed, or a
            selector is invalid. Selector errors are raised at render time.
        ImportError
            If the table is rendered without the optional ``images``
            dependencies installed.
        """
        if j is None:
            raise ValueError(".plot() requires j (column selector)")
        if fun is None:
            raise ValueError(".plot() requires fun (plotting function)")
        if isinstance(height, str):
            height = float(height.replace("em", "").strip())
        self._plot_directives.append(
            PlotDirective(
                i=i,
                j=j,
                regex=regex,
                fun=fun,
                data=data,
                color=color,
                xlim=xlim,
                height=height,
                height_px=height_px,
                width_px=width_px,
                output=output,
            )
        )
        return self

    def images(
        self,
        i: int
        | str
        | Sequence[int | str]
        | pl.Expr
        | pl.Series
        | Callable[[dict], bool]
        | None = None,
        j: _ColumnSelector = None,
        *,
        regex: bool = False,
        paths: list[str] | None = None,
        height: float | str = 1.0,
        output: tuple[str, ...] | None = None,
    ) -> TinyTable:
        """
        Embed existing image files into the selected cells.

        Requires the ``images`` extra (``pip install tytable[images]``).

        Parameters
        ----------
        i, j
            Row/column selectors — see :meth:`style`. ``j`` is required. ``i``
            defaults to *all body rows*.
        paths
            List of image file paths, indexed row-major across the selected
            cells.
        height
            Image height in ``em`` (default ``1.0``).
        output
            Restrict this directive to the given output backends. ``None``
            applies to all.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        ValueError
            If ``j`` or ``paths`` is missing, ``height`` cannot be parsed, or
            a selector is invalid. Selector errors are raised at render time.
        ImportError
            If the table is rendered without the optional ``images``
            dependencies installed.
        """
        if j is None:
            raise ValueError(".images() requires j (column selector)")
        if paths is None:
            raise ValueError(".images() requires paths")
        if isinstance(height, str):
            height = float(height.replace("em", "").strip())
        self._plot_directives.append(
            PlotDirective(
                i=i,
                j=j,
                regex=regex,
                images=list(paths),
                height=height,
                output=output,
            )
        )
        return self

    def group(
        self,
        i: dict[str, int] | list[object] | None = None,
        j: dict[str, list[str | int]] | str | None = None,
    ) -> TinyTable:
        """
        Add row and/or column groups.

        Parameters
        ----------
        i
            Row groups. A ``{label: row}`` dict inserts a labelled separator
            row before the given 0-based data row. A ``list`` (one entry per
            data row) inserts a separator whenever the value changes.
        j
            Column groups. A ``{label: [cols]}`` dict adds a spanning header
            row where each value maps a label to a list of column names or
            positions. A ``str`` delimiter splits every column name and turns
            the shared prefixes into group labels (e.g. ``"_"`` on
            ``"Q1_rev"`` yields a ``"Q1"`` group).

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        TypeError
            If a row-group or column-group specification has an unsupported
            type.
        ValueError
            If a column is missing or a delimiter cannot split every column
            name consistently.

        Examples
        --------
        >>> df = pl.DataFrame({"Q1_rev": [1], "Q1_cost": [2],
        ...                    "Q2_rev": [3], "Q2_cost": [4]})
        >>> (tt(df)                                 # doctest: +SKIP
        ...  .group(j={"Q1": ["Q1_rev", "Q1_cost"],
        ...            "Q2": ["Q2_rev", "Q2_cost"]})
        ...  .group(i={"Section B": 1}))
        """
        if i is not None:
            register_row_groups(self, i)
        if j is not None:
            register_col_groups(self, j, self._colnames)
        return self

    def set_name(
        self,
        j: _ColumnSelector = None,
        *,
        regex: bool = False,
        name: str | Sequence[str],
    ) -> TinyTable:
        """
        Rename column(s) for display without touching the underlying DataFrame.

        Unlike renaming columns in Polars, this only affects the rendered
        header and subsequent ``j`` selectors — the original frame is
        untouched, and arbitrary display names are allowed (including ``""``,
        duplicates, or names that would be awkward as Polars column names).

        Two calling modes:

        - **Per-column**: ``.set_name(j, name=...)`` renames the column(s)
          selected by ``j``. ``j`` follows the same selector rules as
          :meth:`style` / :meth:`fmt` (name, integer position, or a
          list of these). ``regex=True`` enables regex patterns.
          ``name`` is a single ``str`` (applied to every
          matched column, so duplicates are possible) or a ``list[str]`` with
          one entry per matched column.
        - **Full-list replace**: ``.set_name(name=[...])`` (``j`` omitted)
          replaces every column display name; ``name`` must be a list whose
          length equals the number of columns.

        After renaming, subsequent ``j`` selectors use the **new** display
        names — the old Polars column name no longer matches.

        Parameters
        ----------
        j
            Column selector — see :meth:`style`. ``None`` (default) selects
            full-list replace mode (see ``name``).
        name
            New display name. A ``str`` (with ``j`` given) applies to every
            matched column; a ``list[str]`` (with ``j`` given) must match the
            number of matched columns; a ``list[str]`` with ``j=None`` must
            match the total column count.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        TypeError
            If ``name`` is neither a string nor a sequence of strings.
        ValueError
            If ``j`` is missing for a scalar name, a selected column is not
            found, or the number of names does not match the selected columns.

        Examples
        --------
        >>> df = pl.DataFrame({"x": [1], "y": [2]})
        >>> (tt(df)                              # doctest: +SKIP
        ...  .set_name(j="x", name="Variable")
        ...  .set_name(j="y", name="")
        ...  .style(j="Variable", bold=True))

        Replace all headers at once:

        >>> (tt(df)                              # doctest: +SKIP
        ...  .set_name(name=["Alpha", "Beta"]))
        """
        ncol = len(self._colnames)

        if isinstance(name, str):
            if j is None:
                raise ValueError(
                    "set_name(name=str) requires a column selector j; "
                    "pass a list to replace all column names."
                )
            idxs = resolve_j(j, self._colnames, regex=regex)
            for k in idxs:
                self._colnames[k - 1] = name
            return self

        if not isinstance(name, Sequence):
            raise TypeError(
                f"set_name() name must be a string or sequence of strings, "
                f"got {type(name).__name__}"
            )
        names = list(name)
        if not all(isinstance(item, str) for item in names):
            raise TypeError("set_name() name sequence must contain only strings")
        if j is None:
            if len(names) != ncol:
                raise ValueError(
                    f"set_name() full-list replace got {len(names)} name(s) "
                    f"for a {ncol}-column table"
                )
            self._colnames = names
            return self

        idxs = resolve_j(j, self._colnames, regex=regex)
        if len(names) != len(idxs):
            raise ValueError(
                f"set_name() got {len(names)} name(s) for {len(idxs)} selected column(s)"
            )
        for k, nm in zip(idxs, names, strict=True):
            self._colnames[k - 1] = nm
        return self

    def theme(self, name: str | Callable | None = None) -> TinyTable:
        """
        Apply (or re-apply) a theme to the table.

        Parameters
        ----------
        name
            Built-in theme name (``"default"``, ``"striped"``, ``"grid"``,
            ``"empty"``, ``"rotate"``), a callable
            ``theme(table) -> TinyTable``, or ``None`` to apply no theme.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        ValueError
            If ``name`` is not a registered theme name.
        """
        self._apply_theme(name)
        self._theme_name = name
        return self

    def finalize(self, fn: Callable[[str, str], str]) -> TinyTable:
        """
        Register a post-render callback.

        ``fn`` is called after every renderer with ``(rendered_string,
        output)`` and must return the (possibly modified) string. Multiple
        callbacks run in registration order.

        Parameters
        ----------
        fn
            ``fn(rendered: str, output: str) -> str``.

        Returns
        -------
        TinyTable
            ``self``, for chaining.

        Raises
        ------
        Exception
            Any exception raised by ``fn`` is propagated when the table is
            subsequently rendered.
        """
        self._finalize_hooks.append(fn)
        return self

    def render(self, output: str = "typst") -> str:
        """
        Render the table to a string.

        Resolves all recorded directives (style, format, group, plot) and
        produces output for the requested backend, then runs any registered
        ``.finalize()`` callbacks.

        Parameters
        ----------
        output
            ``"typst"`` (default), ``"html"``, or ``"ascii"``.

        Returns
        -------
        str
            The rendered table as a string. Terminal — does not return the
            table.

        Raises
        ------
        TypeError
            If a recorded selector has an unsupported type.
        ValueError
            If a recorded selector, formatting transform, or style is invalid.
        ImportError
            If image directives are present but the optional ``images``
            dependencies are not installed.
        """
        from ._resolve import build

        built = build(self, output)
        renderers: dict[str, Renderer] = {
            "html": HtmlRenderer(),
            "ascii": AsciiRenderer(),
            "typst": TypstRenderer(self._typst_opts),
        }
        renderer = renderers.get(output, renderers["typst"])
        result = renderer.render(built)
        for fn in self._finalize_hooks:
            result = fn(result, output)
        return result

    def save(self, path: str, assets: str | None = None) -> None:
        """
        Render the table and write it to ``path``.

        The output format is inferred from the file suffix: ``.html`` /
        ``.htm`` produce HTML, everything else (typically ``.typ``) produces
        Typst. Parent directories are created automatically.

        Parameters
        ----------
        path
            Destination file path.
        assets
            Where generated image files are written, relative to the output
            file. ``None`` (default) uses a ``tytable_assets/`` folder next to
            the output.

        Raises
        ------
        OSError
            If the destination directory, table file, or generated image
            assets cannot be written.
        TypeError
            If a recorded selector has an unsupported type.
        ValueError
            If a recorded selector, formatting transform, or style is invalid.

        Examples
        --------
        >>> tt(df).save("build/report.typ")               # doctest: +SKIP
        >>> tt(df).save("build/report.html")              # doctest: +SKIP
        >>> tt(df).save("build/tables/x.typ",             # doctest: +SKIP
        ...            assets="../assets/x")
        """
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        if assets is None:
            self._assets_dir = str(p.parent / "tytable_assets")
            self._assets_relpath = "tytable_assets"
        else:
            self._assets_dir = str(p.parent / assets)
            self._assets_relpath = assets.replace("\\", "/")

        suffix = p.suffix.lower()
        out = "html" if suffix in (".html", ".htm") else "typst"
        p.write_text(self.render(out), encoding="utf-8")

    def _repr_html_(self) -> str:
        """Jupyter HTML preview — renders the table as HTML inline."""
        return self.render("html")

    def __repr__(self) -> str:
        """Return an ASCII rendering of the table."""
        return self.render("ascii")
