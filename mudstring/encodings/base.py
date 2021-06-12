from typing import Optional, Union, Dict
from rich.color import Color
from rich.style import Style


class ProtoStyle:
    def __init__(
        self,
        parent: Optional["ProtoStyle"] = None,
        color: Optional[Union[Color, str]] = None,
        bgcolor: Optional[Union[Color, str]] = None,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        blink2: Optional[bool] = None,
        reverse: Optional[bool] = None,
        conceal: Optional[bool] = None,
        strike: Optional[bool] = None,
        underline2: Optional[bool] = None,
        frame: Optional[bool] = None,
        encircle: Optional[bool] = None,
        overline: Optional[bool] = None,
        link: Optional[str] = None,
        tag: Optional[str] = None,
        xml_attr: Optional[Dict[str, str]] = None,
    ):
        self.parent = parent
        self.children = list()
        if parent:
            self.parent.children.append(self)
        self.color = color
        self.bgcolor = bgcolor
        self.bold = bold
        self.dim = dim
        self.italic = italic
        self.underline = underline
        self.blink = blink
        self.blink2 = blink2
        self.reverse = reverse
        self.conceal = conceal
        self.strike = strike
        self.underline2 = underline2
        self.frame = frame
        self.encircle = encircle
        self.overline = overline
        self.link = link
        self.tag = tag
        self.xml_attr = xml_attr

    def ancestors(self, reversed=False):
        """
        Retrieve all ancestors and return it as a list, ordered from outside-to-in.

        Returns:
            ancestors (List[Markup])
        """
        out = list()
        if self.parent:
            parent = self.parent
            out.append(parent)
            while (parent := parent.parent) :
                out.append(parent)
        if reversed:
            out.reverse()
        return out

    def export(self):
        data = self.__dict__.copy()
        data.pop("parent", None)
        data.pop("children", None)
        x = data.pop("xml_attr", None)
        if x:
            data["xml_attr"] = x.copy()
        else:
            data["xml_attr"] = None
        return data

    def inherit_ansi(self):
        for a in self.ancestors():
            self.__dict__.update(a.export())
            return

    def convert(self) -> Style:
        return Style(**self.export())

    def do_reset(self):
        self.color = None
        self.bgcolor = None
        self.bold = None
        self.dim = None
        self.italic = None
        self.underline = None
        self.blink = None
        self.blink2 = None
        self.reverse = None
        self.conceal = None
        self.strike = None
        self.underline2 = None
        self.frame = None
        self.encircle = None
        self.overline = None
        self.link = None
        self.tag = None
        self.xml_attr = None
