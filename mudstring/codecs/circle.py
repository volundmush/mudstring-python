import re
from .. text import Text
from .. markup import Markup, MXPMarkup, ColorMarkup
from typing import Union
from collections import defaultdict


CIRCLE_REGEX = {
    "fg_ansi": re.compile(r"^[xrgObpcwzRGYBPCWvVuUiIsSdD]"),
    "blink_fg_ansi": re.compile(r"^[xrgObpcwzRGYBPCW]"),
    "bg_ansi": re.compile(r"^[xrgObpcWwY]"),
    "xterm_number": re.compile(r"^\[(F|B)[0-5]{3}\]", flags=re.IGNORECASE),
    "xterm_predef": re.compile(r"^[rRgGbByYmMcCwWaAjJlLoOpPtTvV]")
}


def apply_ansi_rule(m: ColorMarkup, mode: str, rule: str):
    pass


def decode(src: str, errors: str = "strict") -> Text:
    idx = list()
    markups = list()
    current = None
    remaining = src
    escaped = None
    data = dict()

    while len(remaining):
        if escaped:
            if escaped == remaining[0]:
                idx.append((current, remaining[0]))
                remaining = remaining[1:]
            elif escaped == '&':
                if (match := CIRCLE_REGEX["fg_ansi"].match(remaining)):
                    current = ColorMarkup(current)
                    markups.append(current)
                    data[current] = {'mode': "fg_ansi", 'rule': remaining[0]}
                    remaining = remaining[1:]
            elif escaped == '`':
                if (match := CIRCLE_REGEX["xterm_number"].match(remaining)):
                    current = ColorMarkup(current)
                    markups.append(current)
                    data[current] = {'mode': 'xterm_number', 'rule': match.group(0)}
                    remaining = remaining[match.end(0):]
                elif (match := CIRCLE_REGEX["xterm_predef"].match(remaining)):
                    current = ColorMarkup(current)
                    markups.append(current)
                    data[current] = {'mode': 'xterm_predef', 'rule': match.group(0)}
                    remaining = remaining[match.end(0):]
            elif escaped == '}':
                if (match := CIRCLE_REGEX["blink_fg_ansi"].match(remaining)):
                    current = ColorMarkup(current)
                    markups.append(current)
                    data[current] = {'mode': 'blink_fg_ansi', 'rule': remaining[0]}
                    remaining = remaining[1:]
            elif escaped == '^':
                if (match := CIRCLE_REGEX["bg_ansi"].match(remaining)):
                    current = ColorMarkup(current)
                    markups.append(current)
                    data[current] = {'mode': 'bg_ansi', 'rule': remaining[0]}
                    remaining = remaining[1:]
            escaped = None
        elif remaining[0] in ('&', '`', '}', '^'):
            escaped = remaining[0]
            remaining = remaining[1:]
        else:
            idx.append((current, remaining[0]))
            remaining = remaining[1:]

    if escaped:
        idx.append((current, escaped))

    for m in markups:
        if isinstance(m, ColorMarkup):
            m.inherit_ansi()
            d = data[m]
            apply_ansi_rule(m, d['mode'], d['rule'])

    return Text.assemble(idx)


def encode(src: Text) -> str:
    return ''


def install():
    Text.install_codec("circle", encode, decode)
