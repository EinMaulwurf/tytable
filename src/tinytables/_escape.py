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


def escape_typst(text):
    if not isinstance(text, str) or not text:
        return text
    if not TYPST_SPECIAL_RE.search(text):
        return text
    return TYPST_SPECIAL_RE.sub(lambda m: TYPST_ESCAPE[m.group(0)], text)
