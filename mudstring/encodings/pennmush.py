from ..patches.style import MudStyle, ProtoStyle
from ..patches.text import MudText
from .colors import COLORS
from colored.hex import HEX
from typing import Union, Tuple, List
from rich.text import Text, Segment, Span
from rich.color import Color
import html
import re
from enum import IntFlag, IntEnum

ANSI_SECTION_MATCH = {
    "letters": re.compile(r"^(?P<data>[a-z ]+)\b", flags=re.IGNORECASE),
    "numbers": re.compile(r"^(?P<data>\d+)\b"),
    "rgb": re.compile(r"^<(?P<red>\d{1,3})\s+(?P<green>\d{1,3})\s+(?P<blue>\d{1,3})>(\b)?"),
    "hex1": re.compile(r"^#(?P<data>[0-9A-F]{6})\b", flags=re.IGNORECASE),
    "hex2": re.compile(r"^<#(?P<data>[0-9A-F]{6})>(\b)?", flags=re.IGNORECASE),
    "name": re.compile(r"^\+(?P<data>\w+)\b", flags=re.IGNORECASE)
}


STYLE_REVERSE = {
    1: "h",
    2: "i",
    4: "f",
    8: "u"
}

class StyleMap(IntFlag):
    BOLD = 1
    INVERSE = 2
    FLASH = 4
    UNDERLINE = 8


class BgMode(IntEnum):
    NONE = 0
    FG = 1
    BG = 2


CHAR_MAP = {
    'f': "flash",
    'h': "bold",
    'i': "reverse",
    'u': "underline"
}


BASE_COLOR_MAP = {
    'd': -1,
    'x': 0,
    'r': 1,
    'g': 2,
    'y': 3,
    'b': 4,
    'm': 5,
    'c': 6,
    'w': 7
}

BASE_COLOR_REVERSE = {v: k for k, v in BASE_COLOR_MAP.items()}

def _process_ground(codes: str, bg: bool = False) -> Tuple[str, Tuple[str, BgMode, object, object]]:
    matched = False
    ground = BgMode.BG if bg else BgMode.FG
    for k, v in ANSI_SECTION_MATCH.items():
        if k == "letters" and ground == BgMode.BG:
            # Letters are not allowed immediately following a /
            continue
        if (match := v.match(codes)):
            codes = codes[match.end():]
            matched = True
            if k == "letters" and ground != BgMode.BG:
                # Letters are not allowed immediately following a /
                return codes, (k, BgMode.NONE, match.groupdict()["data"], match.group(0))
            if k == "numbers":
                data = match.groupdict()["data"]
                number = abs(int(data))
                if number > 255:
                    raise TextError(match.group(0))
                return codes, (k, ground, number, match.group(0))
            if k == "name":
                return codes, (k, ground, match.groupdict()["data"].lower(), match.group(0))
            elif k in ("hex1", "hex2"):
                return codes, (k, ground, '#' + match.groupdict()["data"].upper(), match.group(0))
            elif k == "rgb":
                data = match.groupdict()
                hex = f"#{int(data['red']):2X}{int(data['green']):2X}{int(data['blue']):2X}"
                return codes, (k, ground, hex, match.group(0))
    if not matched:
        raise TextError(codes)


def separate_codes(codes: str, errors: str = "strict"):
    codes = ' '.join(codes.split())

    while len(codes):
        if codes[0] in ('/', '!'):
            codes = codes[1:]
            if not len(codes):
                # if there's nothing after a / then we just break.
                break
            if codes[0].isspace():
                codes = codes[1:]
                # if a space immediately follows a / , then it is treated as no color.
                # it will be ignored.
                continue
            elif codes[0] in ('/', '!'):
                continue
            else:
                remaining, result = _process_ground(codes, True)
                codes = remaining
                yield result

        elif codes[0].isspace():
            codes = codes[1:]
            continue
        else:
            remaining, result = _process_ground(codes, False)
            codes = remaining
            yield result
            matched = False


def test_separate(codes: str):
    for code in separate_codes(codes):
        print(code)


def apply_color_rule(mark: ProtoStyle, rule_tuple):
    mode, g, data, original = rule_tuple
    if mode == "letters":
        for c in data:
            if c == 'n':
                # ANSI reset
                mark.do_reset()
                continue

            if (bit := CHAR_MAP.get(c, None)):
                setattr(mark, bit, True)
            elif (bit := CHAR_MAP.get(c.lower(), None)):
                setattr(mark, bit, False)
            elif (code := BASE_COLOR_MAP.get(c, None)):
                setattr(mark, "color", Color.from_ansi(code))
            elif (code := BASE_COLOR_MAP.get(c.lower(), None)):
                setattr(mark, "bgcolor", Color.from_ansi(code))
            else:
                pass  # I dunno what we got passed, but it ain't relevant.

    elif g == "fg":
        if mode == "numbers":
            mark.set_xterm_fg(data)
        elif mode == "name":
            if (found := COLORS.get(data)):
                mark.set_xterm_fg(found["xterm"])
        elif mode in ("rgb", "hex1", "hex2"):
            mark.set_xterm_fg(int(HEX(data)))
    elif g == "bg":
        if mode == "numbers":
            mark.set_xterm_bg(data)
        elif mode == "name":
            if (found := COLORS.get(data)):
                mark.set_xterm_bg(found["xterm"])
        elif mode in ("rgb", "hex1", "hex2"):
            mark.set_xterm_bg(int(HEX(data)))


def apply_rules(mark: ProtoStyle, rules: str):
    for res in separate_codes(rules):
        apply_color_rule(mark, res)


def apply_mxp(mark: ProtoStyle, rules: str):
    pass


def serialize_colors(s: MudStyle) -> str:
    if c.reset:
        return 'n'

    output = ''
    for k, v in STYLE_REVERSE.items():
        if k & c.bits:
            output += v
        if k & c.off_bits:
            output += v.upper()
    if c.fg_mode == 0:
        output += BASE_COLOR_REVERSE.get(c.fg_color)
    if c.bg_mode == 0:
        output += BASE_COLOR_REVERSE.get(c.bg_color).upper()

    letters = bool(output)

    if c.fg_mode == 1:
        if letters:
            output += ' '
        output += str(c.fg_color)
    if c.bg_mode == 1:
        output += f"/{c.bg_color}"
    return output


def enter_tag(s: MudStyle) -> str:
    if isinstance(m, ColorMarkup):
        return f"{TAG_START}c{serialize_colors(m)}{TAG_END}"
    elif isinstance(m, MXPMarkup):
        if m.attributes:
            attrs = ' '.join([f'{k}="{html.escape(v)}"' for k, v in m.attributes.items()])
            return f"{TAG_START}p{m.tag} {attrs}{TAG_END}"
        else:
            return f"{TAG_START}p{m.tag}{TAG_END}"
    else:
        return ''


def exit_tag(s: MudStyle) -> str:
    if isinstance(m, ColorMarkup):
        return f"{TAG_START}c/{TAG_END}"
    elif isinstance(m, MXPMarkup):
        return f"{TAG_START}p/{TAG_END}"
    else:
        return ''


def encode(mstring: Text, errors: str = "strict") -> str:
    output = ""
    tag_stack = list()
    cur = None

    for i, span in enumerate(mstring.spans):
        if isinstance(span.style, MudStyle):
            if cur:
                # we are already inside of a markup!
                if span.style is cur:
                    pass
                else:
                    # moving to a different markup.
                    if span.style.parent is cur:
                        # we moved into a child.
                        output += enter_tag(span.style)
                        tag_stack.append(span.style)
                    else:
                        # We left a tag and are moving into another kind of tag. It might be a parent, an ancestor,
                        # or completely unrelated. Let's find out which, first!
                        ancestors = cur.ancestors(reversed=True)
                        idx = None

                        if span.style in tag_stack:
                            # We need to close out of the ancestors we no longer have. A slice accomplishes that.
                            tags_we_left = ancestors[tag_stack.index(span.style):]
                            for i in range(len(tags_we_left) - 1):
                                tag_stack.pop(-1)

                            # now that we know what to leave, let's leave them.


                            for tag in reversed(tags_we_left):
                                output += exit_tag(tag)

                        else:
                            # it's not an ancestor at all, so close out of everything and rebuild.
                            for tag in reversed(tag_stack):
                                output += exit_tag(tag)
                            tag_stack.clear()

                            # Now to enter the new tag...

                            for ancestor in span.style.ancestors(reversed=True):
                                output += enter_tag(ancestor)
                                tag_stack.append(ancestor)
                            output += enter_tag(span.style)
                            tag_stack.append(span.style)

                    cur = span.style
            else:
                # We are not inside of a markup tag. Well, that changes now.
                cur = span.style

                for ancestor in span.style.ancestors(reversed=True):
                    tag_stack.append(ancestor)
                tag_stack.append(span.style)

                for tag in tag_stack:
                    output += enter_tag(tag)

        else:
            # we are moving into a None markup...
            if cur:
                for tag in reversed(tag_stack):
                    output += exit_tag(tag)
                tag_stack.clear()
                cur = None
            else:
                # from no markup to no markup. Just append the character.
                pass

        # Then append this span's text
        output += mstring.plain[span.start:span.end]

    # Finalize and exit all remaining tags.
    for tag in reversed(tag_stack):
        output += exit_tag(tag)

    return output


def decode(src, errors: str = "strict") -> Text:
    current = ProtoStyle()
    state = 0
    remaining = src
    segments: List[Tuple[str, MudStyle]] = list()
    tag = None

    while len(remaining):
        if state == 0:
            idx_start = remaining.find('\002')
            if idx_start != -1:
                segments.append((remaining[:idx_start], current.convert()))
                remaining = remaining[idx_start+1:]
                state = 1
            else:
                segments.append((remaining, current.convert()))
                remaining = ''
        elif state == 1:
            # encountered a TAG START...
            tag = remaining[0]
            remaining = remaining[1:]
            state = 2
        elif state == 2:
            # we are inside a tag. hoover up all data up to TAG_END...
            idx_end = remaining.find('\003')
            opening = True
            if idx_end != -1:
                tag_data = remaining[:idx_end]
                remaining = remaining[idx_end+1:]
                if tag_data and tag_data[0] == '/':
                    opening = False
                    tag_data = tag_data[1:]
                if opening:
                    current = ProtoStyle(parent=current)
                    if tag == 'p':
                        apply_mxp(current, tag_data)
                    elif tag == 'c':
                        current.inherit_ansi()
                        apply_rules(current, tag_data)
                else:
                    current = current.parent
                state = 0
            else:
                # malformed data.
                break

    return Text.assemble(*segments)

def ansi_fun_style(code: str) -> MudStyle:
    if code is None:
        code = ''
    code = code.strip()
    mark = ProtoStyle()
    apply_rules(mark, code)
    return mark.convert()


def ansi_fun(code: str, text: Union[Text, str]) -> Text:
    """
    This constructor is used to create a Text from a PennMUSH style ansi() call, such as: ansi(hr,texthere!)
    """
    style = ansi_fun_style(code)
    return ansify(style, text)


def ansify(style: MudStyle, text: Union[Text, str]) -> MudText:
    if isinstance(text, Text):
        return text
    elif isinstance(text, str):
        spans = [Span(0, len(text), style)]
        return MudText(text, spans=spans)


def from_html(text: Union[Text, str], tag: str, **kwargs) -> Text:
    mark = ProtoStyle()
    mark.tag = tag
    mark.xml_attr = kwargs
    if isinstance(text, Text):
        t = [Segment(text.plain[s.start:s.end - s.start], s.style) for s in text.spans]
        return Text.assemble(*t, style=mark.convert())
    elif isinstance(text, str):
        spans = [Span(0, len(text), mark.convert())]
        return Text(text, spans=spans)


def send_menu(text: str, commands=None) -> Text:
    if commands is None:
        commands = []
    hints = '|'.join(a[1] for a in commands)
    cmds = '|'.join(a[0] for a in commands)
    return from_html(text=text, tag='SEND', href=cmds, hint=hints)
