"""Internal semantic text shared by backend-aware formatters."""

from __future__ import annotations

from tytable._escape import escape_html, escape_typst


class _FormattedText(str):
    """Plain callback representation with deferred backend rendering."""

    def render(
        self,
        output: str,
        *,
        escape: bool = True,
        math_mode: bool = False,
        breaks: tuple[str, ...] = (),
    ) -> str:
        raise NotImplementedError


def _render(
    value: object,
    output: str,
    *,
    escape: bool = True,
    math_mode: bool = False,
    breaks: tuple[str, ...] = (),
) -> str:
    if isinstance(value, _FormattedText):
        return value.render(output, escape=escape, math_mode=math_mode, breaks=breaks)
    text = str(value)
    separator = {"typst": " \\ ", "html": "<br>"}.get(output)
    if breaks and separator is not None:
        return separator.join(
            _render(chunk, output, escape=escape, math_mode=math_mode, breaks=breaks[1:])
            for chunk in text.split(breaks[0])
        )
    if not escape or math_mode:
        return text
    return {"typst": escape_typst, "html": escape_html}.get(output, str)(text)


def _strip_math_delimiters(content: str) -> str:
    if content.startswith("$") and content.endswith("$"):
        return content[1:-1].strip()
    return content


class _AffixedText(_FormattedText):
    source: object
    prefix: str
    suffix: str

    def __new__(cls, value: object, prefix: str, suffix: str) -> _AffixedText:
        obj = super().__new__(cls, prefix + str(value) + suffix)
        obj.source, obj.prefix, obj.suffix = value, prefix, suffix
        return obj

    def render(
        self,
        output: str,
        *,
        escape: bool = True,
        math_mode: bool = False,
        breaks: tuple[str, ...] = (),
    ) -> str:
        content = _render(self.source, output, escape=escape, math_mode=math_mode, breaks=breaks)
        if math_mode and output == "typst":
            # Keep affixes literal when a later math formatter interprets the value.
            content = _strip_math_delimiters(content)
            prefix = f"#box[{_render(self.prefix, output, breaks=breaks)}]" if self.prefix else ""
            suffix = f"#box[{_render(self.suffix, output, breaks=breaks)}]" if self.suffix else ""
        else:
            prefix = _render(self.prefix, output, escape=escape, breaks=breaks)
            suffix = _render(self.suffix, output, escape=escape, breaks=breaks)
        return prefix + content + suffix


class _LinebreakText(_FormattedText):
    source: object
    marker: str

    def __new__(cls, value: object, marker: str) -> _LinebreakText:
        obj = super().__new__(cls, str(value))
        obj.source, obj.marker = value, marker
        return obj

    def render(
        self,
        output: str,
        *,
        escape: bool = True,
        math_mode: bool = False,
        breaks: tuple[str, ...] = (),
    ) -> str:
        return _render(
            self.source,
            output,
            escape=escape,
            math_mode=math_mode,
            breaks=(self.marker, *breaks),
        )


class _MathText(_FormattedText):
    source: object
    display: bool

    def __new__(cls, value: object, display: bool) -> _MathText:
        obj = super().__new__(cls, str(value))
        obj.source, obj.display = value, display
        return obj

    def render(
        self,
        output: str,
        *,
        escape: bool = True,
        math_mode: bool = False,
        breaks: tuple[str, ...] = (),
    ) -> str:
        if output != "typst":
            return _render(self.source, output, escape=escape, breaks=breaks)
        content = _strip_math_delimiters(
            _render(self.source, output, escape=False, math_mode=True, breaks=breaks)
        )
        if math_mode:
            return content
        return f"$ {content} $" if self.display else f"${content}$"
