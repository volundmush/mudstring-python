from ..text import Text, TextError, Span
from ..markup import Markup, MXPMarkup, ColorMarkup, _CODES
from ..colors import COLORS
from colored.hex import HEX
from typing import Union
import html
import re
from xml.etree import ElementTree as ET
from collections import defaultdict

TAG_START = '\002'
TAG_END = '\003'
MARKUP_START = TAG_START
MARKUP_END = TAG_END


NEW_MATCH = {
    _CODES.CS_HEX: re.compile(r"^#(?P<data>[0-9A-F]{6})$", flags=re.IGNORECASE),
    _CODES.CS_RGBHEX: re.compile(r"^<#(?P<data>[0-9A-F]{6})>$", flags=re.IGNORECASE),
    _CODES.CS_RGB: re.compile(r"^<(?P<red>[0-9]{1,3}) +(?P<green>[0-9]{1,3}) +(?P<blue>[0-9]{1,3})>$"),
    _CODES.CS_NAME: re.compile(r"^\+(?P<name>\w+)\b", flags=re.IGNORECASE)
}


ANSI_SECTION_MATCH = {
    "letters": re.compile(r"^(?P<data>[a-z ]+)\b", flags=re.IGNORECASE),
    "numbers": re.compile(r"^(?P<data>\d+)\b"),
    "rgb": re.compile(r"^<(?P<red>\d{1,3})\s+(?P<green>\d{1,3})\s+(?P<blue>\d{1,3})>(\b)?"),
    "hex1": re.compile(r"^#(?P<data>[0-9A-F]{6})\b", flags=re.IGNORECASE),
    "hex2": re.compile(r"^<#(?P<data>[0-9A-F]{6})>(\b)?", flags=re.IGNORECASE),
    "name": re.compile(r"^\+(?P<data>\w+)\b", flags=re.IGNORECASE)
}


CHAR_MAP = {
    'f': "flash",
    'h': "hilite",
    'i': "invert",
    'u': "underscore"
}


STYLE_REVERSE = {
    1: "h",
    2: "i",
    4: "f",
    8: "u"
}


BASE_COLOR_MAP = {
    'd': -1,
    'x': 30,
    'r': 31,
    'g': 32,
    'y': 33,
    'b': 34,
    'm': 35,
    'c': 36,
    'w': 37
}

BASE_COLOR_REVERSE = {v: k for k, v in BASE_COLOR_MAP.items()}


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
                matched = False
                for k, v in ANSI_SECTION_MATCH.items():
                    if k == "letters":
                        # Letters are not allowed immediately following a /
                        continue
                    if (match := v.match(codes)):
                        codes = codes[match.end():]
                        matched = True
                        if k == "numbers":
                            data = match.groupdict()["data"]
                            number = abs(int(data))
                            if number > 255:
                                raise TextError(match.group(0))
                            yield (k, "bg", number, match.group(0))
                            break
                        if k == "name":
                            yield (k, "bg", match.groupdict()["data"].lower(), match.group(0))
                            break
                        elif k in ("hex1", "hex2"):
                            yield (k, "bg", '#' + match.groupdict()["data"].upper(), match.group(0))
                            break
                        elif k == "rgb":
                            data = match.groupdict()
                            hex = f"#{int(data['red']):2X}{int(data['green']):2X}{int(data['blue']):2X}"
                            yield (k, "bg", hex, match.group(0))
                            break
                if not matched:
                    raise TextError(codes)

        elif codes[0].isspace():
            codes = codes[1:]
            continue
        else:
            matched = False
            for k, v in ANSI_SECTION_MATCH.items():
                if (match := v.match(codes)):
                    codes = codes[match.end():]
                    matched = True
                    if k == "letters":
                        # letters are the one exception to most rules:
                        # they can be either fg or BG.
                        yield (k, None, match.groupdict()["data"], match.group(0))
                        break
                    if k == "name":
                        yield (k, "fg", match.groupdict()["data"].lower(), match.group(0))
                        break
                    if k == "numbers":
                        data = match.groupdict()["data"]
                        number = abs(int(data))
                        if number > 255:
                            raise TextError(match.group(0))
                        yield (k, "fg", number, match.group(0))
                        break
                    elif k in ("hex1", "hex2"):
                        yield (k, "fg", '#' + match.groupdict()["data"], match.group(0))
                        break
                    elif k == "rgb":
                        data = match.groupdict()
                        hexcodes = f"#{int(data['red']):2X}{int(data['green']):2X}{int(data['blue']):2X}"
                        yield (k, "fg", hexcodes, match.group(0))
                        break

            if not matched:
                raise TextError(codes)


def test_separate(codes: str):
    for code in separate_codes(codes):
        print(code)


def apply_color_rule(mark: ColorMarkup, rule_tuple):
    mode, g, data, original = rule_tuple
    if mode == "letters":
        for c in data:
            if c == 'n':
                # ANSI reset
                mark.do_reset()
                continue

            if (bit := CHAR_MAP.get(c, None)):
                mark.apply_style(bit)
            elif (bit := CHAR_MAP.get(c.lower(), None)):
                mark.remove_style(bit)
            elif (code := BASE_COLOR_MAP.get(c, None)):
                mark.set_ansi_fg(code)
            elif (code := BASE_COLOR_MAP.get(c.lower(), None)):
                mark.set_ansi_bg(code + 10)
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


def apply_rules(mark: ColorMarkup, rules: str):
    for res in separate_codes(rules):
        apply_color_rule(mark, res)


def serialize_colors(c: ColorMarkup) -> str:
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


def enter_tag(m: Markup) -> str:
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


def exit_tag(m: Markup) -> str:
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
        if isinstance(span.style, Markup):
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
    markup = list()
    idx = list()

    state, index = 0, None
    mstack = list()
    tag = ""
    counter = -1
    data = defaultdict(str)

    for s in src:
        if state == 0:
            if s == TAG_START:
                state = 1
            else:
                idx.append((index, s))
        elif state == 1:
            # Encountered a TAG START...
            tag = s
            state = 2
        elif state == 2:
            # we are just inside a tag. if it begins with / this is a closing. else, opening.
            if s == "/":
                state = 4
            else:
                state = 3
                counter += 1
                if tag == 'p':
                    mark = MXPMarkup(index)
                elif tag == 'c':
                    mark = ColorMarkup(index)
                else:
                    raise TextError(f"Unsupported PennMush markup tag: {tag}")
                markup.append(mark)
                index = mark
                data[mark] += s
                mstack.append(mark)
        elif state == 3:
            # we are inside an opening tag, gathering text. continue until TAG_END.
            if s == TAG_END:
                state = 0
            else:
                data[mstack[-1]] += s
        elif state == 4:
            # we are inside a closing tag, gathering text. continue until TAG_END.
            if s == TAG_END:
                state = 0
                mark = mstack.pop()
                index = mark.parent
            else:
                data[mstack[-1]] += s

    for m in markup:
        if isinstance(m, ColorMarkup):
            m.inherit_ansi()
            apply_rules(m, data[m])
        elif isinstance(m, MXPMarkup):
            found = data[m]
            tag = found
            if ' ' in found:
                tag, extra = found.split(' ', 1)
            root = ET.fromstring(f'<{found}></{tag}>')
            m.setup(root.tag, root.attrib)

    return Text.assemble(idx)


def ansi_fun(code: str, text: Union[Text, str]) -> Text:
    """
    This constructor is used to create a Text from a PennMUSH style ansi() call, such as: ansi(hr,texthere!)
    """
    code = code.strip()
    mark = ColorMarkup()
    apply_rules(mark, code)
    if isinstance(text, Text):
        return decode(f"{enter_tag(mark)}{encode(text)}{exit_tag(mark)}")
    elif isinstance(text, str):
        return Text(src=text, spans=[Span(0, len(text), mark)])


def from_html(text: Union[Text, str], tag: str, **kwargs) -> Text:
    mark = MXPMarkup()
    mark.setup(tag.strip(), kwargs)
    if isinstance(text, Text):
        return decode(f"{enter_tag(mark)}{encode(text)}{exit_tag(mark)}")
    else:
        return Text(src=text, spans=[Span(0, len(text), mark)])


def send_menu(text: str, commands=None) -> Text:
    if commands is None:
        commands = []
    hints = '|'.join(a[1] for a in commands)
    cmds = '|'.join(a[0] for a in commands)
    return from_html(text=text, tag='SEND', href=cmds, hint=hints)


def install():
    Text.install_codec("pennmush", encode, decode)