import html
from rich import style
from typing import Optional
from rich.color import ColorSystem


OLD_STYLE = style.Style


class MudStyle(OLD_STYLE):
    _tag: str
    _xml_attr: str

    __slots__ = ['_tag', '_xml_attr']

    def __init__(self, *args, **kwargs):
        self._tag = kwargs.pop('tag', '')
        if (xml_attr := kwargs.pop('xml_attr', None)):
            self._xml_attr = ' '.join(f'{k}="{html.escape(v)}"' for k, v in xml_attr.items()) if xml_attr else ''
        else:
            self._xml_attr = ''
        super().__init__(*args, **kwargs)
        self._hash = hash(
            (
                self._color,
                self._bgcolor,
                self._attributes,
                self._set_attributes,
                self._link,
                self._tag,
                self._xml_attr
            )
        )

    def __add__(self, style):
        if not (isinstance(style, OLD_STYLE) or style is None):
            raise NotImplementedError()  # type: ignore
        if style is None or style._null:
            return self
        if self._null:
            return style
        new_style = self.__new__(self.__class__)
        new_style._ansi = None
        new_style._style_definition = None
        new_style._color = style._color or self._color
        new_style._bgcolor = style._bgcolor or self._bgcolor
        new_style._attributes = (self._attributes & ~style._set_attributes) | (
            style._attributes & style._set_attributes
        )
        new_style._set_attributes = self._set_attributes | style._set_attributes
        new_style._link = style._link or self._link
        new_style._link_id = style._link_id or self._link_id
        new_style._hash = style._hash
        new_style._null = self._null or style._null
        if hasattr(style, "_tag"):
            new_style._tag = style._tag
            new_style._xml_attr = style._xml_attr
        else:
            new_style._tag = self._tag
            new_style._xml_attr = self._xml_attr
        return new_style

    @classmethod
    def upgrade(cls, style):
        if not (isinstance(style, OLD_STYLE) or style is None):
            raise NotImplementedError()  # type: ignore
        up_style = cls.__new__(cls)
        for s in OLD_STYLE.__slots__:
            setattr(up_style, s, getattr(style, s))
        up_style._tag = ''
        up_style._xml_attr = ''
        return up_style

    def __radd__(self, other):
        return self.__class__.upgrade(other) + self

    def render(
        self,
        text: str = "",
        *,
        color_system: Optional[ColorSystem] = ColorSystem.TRUECOLOR,
        legacy_windows: bool = False,
        mxp: bool = False,
        links: bool = True
    ) -> str:
        """Render the ANSI codes for the style.

        Args:
            text (str, optional): A string to style. Defaults to "".
            color_system (Optional[ColorSystem], optional): Color system to render to. Defaults to ColorSystem.TRUECOLOR.

        Returns:
            str: A string containing ANSI style codes.
        """
        out_text = html.escape(text) if mxp else text
        if not out_text:
            return out_text
        if color_system is not None:
            attrs = self._make_ansi_codes(color_system)
            rendered = f"\x1b[{attrs}m{out_text}\x1b[0m" if attrs else out_text
        else:
            rendered = out_text
        if links and self._link and not legacy_windows:
            rendered = f"\x1b]8;id={self._link_id};{self._link}\x1b\\{rendered}\x1b]8;;\x1b\\"
        if mxp and self._tag:
            if self._xml_attr:
                rendered = f"\x1b]4z<{self._tag} {self._xml_attr}>{rendered}\x1b]4z</{self._tag}>"
            else:
                rendered = f"\x1b]4z<{self._tag}>{rendered}\x1b]4z</{self._tag}>"
        return rendered

OLD_NULL = style.NULL_STYLE