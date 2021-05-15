import re
from rich.text import Text
from ..patches.style import MudStyle, ProtoStyle
from rich.color import Color
from typing import Union, List, Tuple


LETTERS = {
    'x': Color.from_ansi(0),
    'r': Color.from_ansi(1),
    'g': Color.from_ansi(2),
    'y': Color.from_ansi(3),
    'b': Color.from_ansi(4),
    'm': Color.from_ansi(5),
    'c': Color.from_ansi(6),
    'w': Color.from_ansi(7)
}


EV_REGEX = {
    "fg_ansi_bold": re.compile(r"^(r|g|y|b|m|c|x|w)"),
    "fg_ansi_normal": re.compile(r"^(R|G|Y|B|M|C|X|W)"),
    "bg_ansi_bold": re.compile(r"^\[(r|g|y|b|m|c|x|w)"),
    "bg_ansi_normal": re.compile(r"^\[(R|G|Y|B|M|C|X|W)"),
    "fg_xterm": re.compile(r"^[0-5]{3}"),
    "bg_xterm": re.compile(r"^\[([0-5]{3})")
}


def apply_fg_ansi_bold(proto: ProtoStyle, code):
    proto.bold = True
    proto.color = LETTERS[code.group(0)]


def apply_fg_ansi_normal(proto: ProtoStyle, code):
    proto.color = LETTERS[code.group(0).lower()]


def apply_bg_ansi_bold(proto: ProtoStyle, code):
    proto.bold = True
    proto.bgcolor = LETTERS[code.group(0)]


def apply_bg_ansi_normal(proto: ProtoStyle, code):
    proto.bgcolor = LETTERS[code.group(0).lower()]


def apply_fg_xterm(proto: ProtoStyle, code):
    pass


def apply_bg_xterm(proto: ProtoStyle, code):
    pass


EV_APPLY = {
    "fg_ansi_bold": apply_fg_ansi_bold,
    "fg_ansi_normal": apply_fg_ansi_normal,
    "bg_ansi_bold": apply_bg_ansi_bold,
    "bg_ansi_normal": apply_bg_ansi_normal,
    "fg_xterm": apply_fg_xterm,
    "bg_xterm": apply_bg_xterm
}


def apply_ansi_style(proto: ProtoStyle, code: str):
    if code == 'h':
        proto.bold = True
    elif code == 'H':
        proto.bold = False
    elif code == '*':
        proto.reverse = True
    elif code == 'u':
        proto.underline = True
    elif code == '^':
        proto.blink = True
    elif code == 'n':
        proto.do_reset()


CHAR_SUBS = {
    '-': '\t',
    '_': ' ',
    '/': '\n',
    '>': '    ',
    '|': '|'
}


def decode(src: str, errors: str = "strict") -> Text:
    current = ProtoStyle()
    segment: str = ""

    remaining = src
    escaped: bool = False
    segments: List[Tuple[str, MudStyle]] = list()

    while len(remaining):
        if escaped:
            if (sub_char := CHAR_SUBS.get(remaining[0], None)):
                segment += sub_char
                remaining = remaining[1:]
            elif remaining[0] in ('n', 'N'):
                if segment:
                    segments.append((segment, current.convert()))
                    segment = ''
                current = ProtoStyle(parent=current)
                current.do_reset()
                remaining = remaining[1:]
            elif remaining[0] in ('h', 'H', '*', 'u', '^'):
                if segment:
                    segments.append((segment, current.convert()))
                    segment = ''
                current = ProtoStyle(parent=current)
                current.inherit_ansi()
                apply_ansi_style(current, remaining[0])
                remaining = remaining[1:]
            else:
                for name, pattern in EV_REGEX.items():
                    if (match := pattern.match(remaining)):
                        if segment:
                            segments.append((segment, current.convert()))
                            segment = ''
                        current = ProtoStyle(parent=current)
                        current.inherit_ansi()
                        EV_APPLY[name](current, match)
                        remaining = remaining[match.end(0):]
                        break
            escaped = False
        else:
            loc = remaining.find('|')
            if loc != -1:
                segment += remaining[:loc]
                remaining = remaining[loc+1:]
                escaped = True
            else:
                segment += remaining
                remaining = ''

    if segment:
        segments.append((segment, current.convert()))

    return Text.assemble(*[(t, s) for t, s in segments])


def encode(src: Text) -> str:
    return ''
