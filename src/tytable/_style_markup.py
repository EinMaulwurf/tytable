"""Shared translation of resolved style properties into renderer markup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tytable._colors import color_to_css, color_to_typst
from tytable._styling import align_to_typst

_UNSAFE_TYPST_SIGNATURE_CHARS = frozenset("#();[]")
_MISSING = object()


def align_to_css(horizontal: str | None, vertical: str | None) -> str | None:
    """Translate alignment shorthands into CSS alignment keywords."""
    if vertical in ("m", "horizon"):
        vertical = "middle"
    parts: list[str] = []
    if horizontal:
        parts.append({"l": "left", "c": "center", "r": "right"}.get(horizontal, horizontal))
    if vertical:
        parts.append({"t": "top", "b": "bottom"}.get(vertical, vertical))
    return " ".join(parts) if parts else None


@dataclass(frozen=True, slots=True)
class StyleMarkup:
    """Normalized style properties with projections for Typst and HTML.

    Keeping the source mapping here preserves the distinction between a missing
    property and an explicitly false or ``None`` value. That distinction is part
    of the renderers' existing output contract for color, size, and rotation.
    """

    props: dict[str, Any]

    @classmethod
    def from_props(cls, props: dict[str, Any]) -> StyleMarkup:
        """Create a style translation from a resolved property mapping."""
        return cls(props.copy())

    def typst_signature(self) -> str:
        """Return Typst cell-style arguments, including the trailing comma."""
        self._validate_typst_signature_values()
        props = self.props
        parts: list[str] = []
        if props.get("bold"):
            parts.append("bold: true")
        if props.get("italic"):
            parts.append("italic: true")
        if props.get("underline"):
            parts.append("underline: true")
        if props.get("strikeout"):
            parts.append("strikeout: true")
        if props.get("monospace"):
            parts.append("mono: true")
        if props.get("smallcaps"):
            parts.append("smallcaps: true")
        if "color" in props:
            parts.append(f"color: {color_to_typst(props['color'])}")
        if "background" in props:
            parts.append(f"background: {color_to_typst(props['background'])}")
        if "fontsize" in props:
            parts.append(f"fontsize: {props['fontsize']}em")
        if "indent" in props and props["indent"] > 0:
            parts.append(f"indent: {props['indent']}em")
        if "padding" in props:
            parts.append(f"padding: {self._padding_to_typst(props['padding'])}")
        if "rotate" in props:
            parts.append(f"rotate: {props['rotate']}deg")
        align = align_to_typst(props.get("align"), props.get("alignv"))
        if align:
            parts.append(f"align: {align}")
        return ", ".join(parts) + "," if parts else ""

    def typst_inline(self, content: str) -> str:
        """Wrap escaped content in Typst text-level styling."""
        props = self.props
        args: list[str] = []
        if props.get("fontsize") is not None:
            args.append(f"size: {props['fontsize']}em")
        if "color" in props:
            args.append(f"fill: {color_to_typst(props['color'])}")
        if props.get("italic"):
            args.append('style: "italic"')
        if props.get("bold"):
            args.append('weight: "bold"')
        out = f"text({', '.join(args)}, [{content}])" if args else f"[{content}]"
        if props.get("underline"):
            out = f"underline({out})"
        if props.get("strikeout"):
            out = f"strike({out})"
        if props.get("smallcaps"):
            out = f"smallcaps({out})"
        if props.get("indent") and props["indent"] > 0:
            out = f"pad(left: {props['indent']}em, {out})"
        return out

    def html_cell_css(self, border_css: str = "") -> str:
        """Return CSS declarations for a table cell."""
        props = self.props
        parts = [border_css] if border_css else []
        declarations = (
            ("bold", "font-weight:bold"),
            ("italic", "font-style:italic"),
            ("underline", "text-decoration:underline"),
            ("strikeout", "text-decoration:line-through"),
            ("monospace", "font-family:monospace"),
            ("smallcaps", "font-variant:small-caps"),
        )
        parts.extend(css for prop, css in declarations if props.get(prop))
        self._append_css_value(parts, "color", "color")
        self._append_css_value(parts, "background", "background-color")
        self._append_css_value(parts, "fontsize", "font-size", suffix="em")
        if "padding" in props:
            parts.append(f"padding:{self._padding_to_css(props['padding'])}")
        if "indent" in props and props["indent"] > 0:
            if "padding" in props:
                left = self._padding_left(props["padding"])
                parts.append(f"padding-left:calc({left}em + {props['indent']}em)")
            else:
                parts.append(f"padding-left:{props['indent']}em")
        if "rotate" in props:
            parts.extend((f"transform:rotate({props['rotate']}deg)", "white-space:nowrap"))
        align = align_to_css(props.get("align"), None)
        if align:
            parts.append(f"text-align:{align}")
        alignv = align_to_css(None, props.get("alignv"))
        if alignv:
            parts.append(f"vertical-align:{alignv}")
        return "; ".join(parts)

    def html_inline(self, content: str) -> str:
        """Wrap escaped content in HTML inline styling."""
        props = self.props
        parts: list[str] = []
        if props.get("smallcaps"):
            parts.append("font-variant:small-caps")
        self._append_css_value(parts, "color", "color")
        self._append_css_value(parts, "fontsize", "font-size", suffix="em")
        if props.get("monospace"):
            parts.append("font-family:monospace")
        if props.get("background"):
            parts.append(f"background-color:{color_to_css(props['background'])}")
        if props.get("indent") and props["indent"] > 0:
            parts.append(f"padding-left:{props['indent']}em")
        out = f'<span style="{";".join(parts)}">{content}</span>' if parts else content
        for prop, tag in (("italic", "i"), ("strikeout", "s"), ("underline", "u"), ("bold", "b")):
            if props.get(prop):
                out = f"<{tag}>{out}</{tag}>"
        return out

    def _append_css_value(
        self, parts: list[str], prop: str, css_name: str, *, suffix: str = ""
    ) -> None:
        value = self.props.get(prop, _MISSING)
        if value is not _MISSING:
            if prop in ("color", "background"):
                value = color_to_css(value)
            parts.append(f"{css_name}:{value}{suffix}")

    @staticmethod
    def _padding_to_typst(value: float | tuple[float, ...]) -> str:
        """Translate normalized padding into a Typst inset expression."""
        if isinstance(value, int | float):
            return f"{value}em"
        if len(value) == 2:
            vertical, horizontal = value
            return f"(y: {vertical}em, x: {horizontal}em)"
        top, right, bottom, left = value
        return f"(top: {top}em, right: {right}em, bottom: {bottom}em, left: {left}em)"

    @staticmethod
    def _padding_to_css(value: float | tuple[float, ...]) -> str:
        """Translate normalized padding into a CSS shorthand value."""
        if isinstance(value, int | float):
            return f"{value}em"
        return " ".join(f"{item}em" for item in value)

    @staticmethod
    def _padding_left(value: float | tuple[float, ...]) -> float:
        """Return the normalized left padding component."""
        if isinstance(value, int | float):
            return value
        if len(value) == 2:
            return value[1]
        return value[3]

    def _validate_typst_signature_values(self) -> None:
        for name, value in self.props.items():
            if not isinstance(value, str):
                continue
            if name in ("color", "background"):
                color_to_typst(value)
            elif any(char in value for char in _UNSAFE_TYPST_SIGNATURE_CHARS):
                raise ValueError(f"unsafe Typst style property {name!r}: {value!r}")
