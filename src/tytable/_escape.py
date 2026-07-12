"""Escaping for Typst and HTML metacharacters in cell text and captions."""

from __future__ import annotations

import re

TYPST_ESCAPE = {
    "\\": "\\\\",
    "<": "\\<",
    ">": "\\>",
    "*": "\\*",
    "_": "\\_",
    "@": "\\@",
    "=": "\\=",
    "-": "\\-",
    "+": "\\+",
    "/": "\\/",
    "$": "\\$",
    "#": "\\#",
    "[": "\\[",
    "]": "\\]",
}
TYPST_SPECIAL_RE = re.compile(r"[\\<>*_@=+/\$#\[\]\-]")

HTML_ESCAPE = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
}
HTML_SPECIAL_RE = re.compile(r"[&<>]")


def escape_typst(text: str) -> str:
    """Backslash-escape Typst metacharacters in ``text`` (no-op when none are present)."""
    if not isinstance(text, str) or not text:
        return text
    if not TYPST_SPECIAL_RE.search(text):
        return text
    return TYPST_SPECIAL_RE.sub(lambda m: TYPST_ESCAPE[m.group(0)], text)


def escape_html(text: str) -> str:
    """Escape ``&``, ``<``, ``>`` for safe inclusion in HTML text."""
    if not isinstance(text, str) or not text:
        return text
    if not HTML_SPECIAL_RE.search(text):
        return text
    return HTML_SPECIAL_RE.sub(lambda m: HTML_ESCAPE[m.group(0)], text)
