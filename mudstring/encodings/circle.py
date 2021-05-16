import re
from ..patches.style import MudStyle, ProtoStyle
from rich.text import Text
from typing import Union, List, Tuple, Iterable, Optional
from collections import defaultdict


CIRCLE_REGEX = {
    "fg_ansi": re.compile(r"^[xrgObpcwzRGYBPCWvVuUiIsSdD]"),
    "blink_fg_ansi": re.compile(r"^[xrgObpcwzRGYBPCW]"),
    "bg_ansi": re.compile(r"^[xrgObpcWwY]"),
    "xterm_number": re.compile(r"^\[(F|B)[0-5]{3}\]", flags=re.IGNORECASE),
    "xterm_predef": re.compile(r"^[rRgGbByYmMcCwWaAjJlLoOpPtTvV]")
}


def find_first(within: str, chars: Iterable[str]):
    results = list()
    for c in chars:
        f = within.find(c)
        if f != -1:
            results.append(f)
    if results:
        return min(results)
    else:
        return -1


def apply_ansi_rule(proto: ProtoStyle, mode: str, rule: str):
    pass


def decode(src: str, errors: str = "strict") -> Text:
    current = ProtoStyle()
    segment: str = ""

    remaining = src
    escaped: Optional[str] = None
    segments: List[Tuple[str, MudStyle]] = list()

    while len(remaining):
        if escaped:
            if escaped == remaining[0]:
                segment += remaining[0]
                remaining = remaining[1:]
            elif escaped == '&':
                if (match := CIRCLE_REGEX["fg_ansi"].match(remaining)):
                    if segment:
                        segments.append((segment, current.convert()))
                        segment = ''
                    current = ProtoStyle(current)
                    if remaining[0].upper() != 'D':
                        current.inherit_ansi()
                        apply_ansi_rule(current, "fg_ansi", remaining[0])
                    else:
                        current.reset = True
                    remaining = remaining[1:]
            elif escaped == '`':
                if (match := CIRCLE_REGEX["xterm_number"].match(remaining)):
                    if segment:
                        segments.append((segment, current.convert()))
                        segment = ''
                    current = ProtoStyle(current)
                    apply_ansi_rule(current, "xterm_number", match.group(0))
                    remaining = remaining[match.end(0):]
                elif (match := CIRCLE_REGEX["xterm_predef"].match(remaining)):
                    if segment:
                        segments.append((segment, current.convert()))
                        segment = ''
                    current = ProtoStyle(current)
                    apply_ansi_rule(current, "xterm_predef", match.group(0))
                    remaining = remaining[match.end(0):]
            elif escaped == '}':
                if (match := CIRCLE_REGEX["blink_fg_ansi"].match(remaining)):
                    if segment:
                        segments.append((segment, current.convert()))
                        segment = ''
                    current = ProtoStyle(current)
                    apply_ansi_rule(current, "blink_fg_ansi", remaining[0])
                    remaining = remaining[1:]
            elif escaped == '^':
                if (match := CIRCLE_REGEX["bg_ansi"].match(remaining)):
                    if segment:
                        segments.append((segment, current.convert()))
                        segment = ''
                    current = ProtoStyle(current)
                    apply_ansi_rule(current, "bg_ansi", remaining[0])
                    remaining = remaining[1:]
            escaped = None
        else:
            loc = find_first(remaining, ('&', '`', '}', '^'))
            if loc != -1:
                escaped = remaining[loc]
                segment += remaining[:loc]
                remaining = remaining[loc+1:]
            else:
                segment += remaining
                remaining = ''

    if segment:
        segments.append((segment, current.convert()))

    return Text.assemble(*[(t, s) for t, s in segments])


def encode(src: Text) -> str:
    return ''


def install():
    Text.install_codec("circle", encode, decode)
