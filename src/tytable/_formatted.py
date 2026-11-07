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


class _DisplayText(str):
    """Current backend string retaining its semantic source for built-ins."""

    source: _FormattedText

    def __new__(cls, text: str, source: _FormattedText) -> _DisplayText:
        obj = super().__new__(cls, text)
        obj.source = source
        return obj


def _source(value: object) -> object:
    return value.source if isinstance(value, _DisplayText) else value


def _render(
    value: object,
    output: str,
    *,
    escape: bool = True,
    math_mode: bool = False,
    breaks: tuple[str, ...] = (),
) -> str:
    value = _source(value)
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


class _LinebreakText(_FormattedText):
    source: object
    marker: str

    def __new__(cls, value: object, marker: str) -> _LinebreakText:
        value = _source(value)
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
        value = _source(value)
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
        content = _render(self.source, output, escape=False, math_mode=True, breaks=breaks)
        if content.startswith("$") and content.endswith("$"):
            content = content[1:-1].strip()
        if math_mode:
            return content
        return f"$ {content} $" if self.display else f"${content}$"
