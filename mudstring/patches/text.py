from rich import text
from rich.text import Span
from typing import List, Set, Union, Dict, Tuple, Optional
from . style import MudStyle, OLD_STYLE
import re

import random

OLD_TEXT = text.Text

_RE_SQUISH = re.compile("\S+")
_RE_NOTSPACE = re.compile("[^ ]+")

class MudText(text.Text):

    def __iadd__(self, other):
        self.append(other)
        return self

    def __radd__(self, other):
        if isinstance(other, str):
            return self.__class__(text=other) + self
        return NotImplemented

    def __mul__(self, other):
        if not isinstance(other, int):
            return self
        if other <= 0:
            return self.__class__()
        if other == 1:
            return self.copy()
        if other > 1:
            out = self.copy()
            for i in range(other-1):
                out.append(self)
            return out

    def __rmul__(self, other):
        if not isinstance(other, int):
            return self
        return self * other

    def __format__(self, format_spec):
        return self.plain.__format__(format_spec)

    def capitalize(self):
        return self.__class__(text=self.plain.capitalize(), spans=list(self.spans))

    def count(self, *args, **kwargs):
        return self.plain.count(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        return self.plain.startswith(*args, **kwargs)

    def endswith(self, *args, **kwargs):
        return self.plain.endswith(*args, **kwargs)

    def find(self, *args, **kwargs):
        return self.plain.find(*args, **kwargs)

    def index(self, *args, **kwargs):
        return self.plain.index(*args, **kwargs)

    def isalnum(self):
        return self.plain.isalnum()

    def isalpha(self):
        return self.plain.isalpha()

    def isdecimal(self):
        return self.plain.isdecimal()

    def isdigit(self):
        return self.plain.isdigit()

    def isidentifier(self):
        return self.plain.isidentifier()

    def islower(self):
        return self.plain.islower()

    def isnumeric(self):
        return self.plain.isnumeric()

    def isprintable(self):
        return self.plain.isprintable()

    def isspace(self):
        return self.plain.isspace()

    def istitle(self):
        return self.plain.istitle()

    def isupper(self):
        return self.plain.isupper()

    def center(self, width, fillchar=' '):
        changed = self.plain.center(width, fillchar)
        start = changed.find(self.plain)
        lside = changed[:start]
        rside = changed[len(lside)+len(self.plain):]
        idx = self.disassemble_bits()
        new_idx = list()
        for c in lside:
            new_idx.append((None, c))
        new_idx.extend(idx)
        for c in rside:
            new_idx.append((None, c))
        return self.__class__.assemble_bits(new_idx)

    def ljust(self, width: int, fillchar: Union[str, "MudText"] = ' '):
        diff = width - len(self)
        out = self.copy()
        if diff <= 0:
            return out
        else:
            if isinstance(fillchar, str):
                fillchar = MudText(fillchar)
            out.append(fillchar * diff)
            return out

    def rjust(self, width: int, fillchar: Union[str, "MudText"] = ' '):
        diff = width - len(self)
        if diff <= 0:
            return self.copy()
        else:
            if isinstance(fillchar, str):
                fillchar = MudText(fillchar)
            out = fillchar * diff
            out.append(self)
            return out

    def lstrip(self, chars: str = None):
        lstripped = self.plain.lstrip(chars)
        strip_count = len(self.plain) - len(lstripped)
        return self[strip_count:]

    def strip(self, chars: str = ' '):
        out_map = self.disassemble_bits()
        for i, e in enumerate(out_map):
            if e[1] != chars:
                out_map = out_map[i:]
                break
        out_map.reverse()
        for i, e in enumerate(out_map):
            if e[1] != chars:
                out_map = out_map[i:]
                break
        out_map.reverse()
        return self.__class__.assemble_bits(out_map)

    def replace(self, old: str, new: Union[str, text.Text], count=None):
        if not (indexes := self.find_all(old)):
            return self.clone()
        if count and count > 0:
            indexes = indexes[:count]
        old_len = len(old)
        new_len = len(new)
        other = self.clone()
        markup_idx_map = self.disassemble_bits()
        other_map = other.disassemble_bits()

        for idx in reversed(indexes):
            final_markup = markup_idx_map[idx + old_len][0]
            diff = abs(old_len - new_len)
            replace_chars = min(new_len, old_len)
            # First, replace any characters that overlap.
            for i in range(replace_chars):
                other_map[idx + i] = (markup_idx_map[idx + i][0], new[i])
            if old_len == new_len:
                pass  # the nicest case. nothing else needs doing.
            elif old_len > new_len:
                # slightly complex. pop off remaining characters.
                for i in range(diff):
                    deleted = other_map.pop(idx + new_len)
            elif new_len > old_len:
                # slightly complex. insert new characters.
                for i in range(diff):
                    other_map.insert(idx + old_len + i, (final_markup, new[old_len + i]))

        return self.__class__.assemble_bits(other_map)

    def find_all(self, sub: str):
        indexes = list()
        start = 0
        while True:
            start = self.plain.find(sub, start)
            if start == -1:
                return indexes
            indexes.append(start)
            start += len(sub)

    def scramble(self):
        idx = self.disassemble_bits()
        random.shuffle(idx)
        return self.__class__.assemble_bits(idx)

    def reverse(self):
        idx = self.disassemble_bits()
        idx.reverse()
        return self.__class__.assemble_bits(idx)

    @classmethod
    def assemble_bits(cls, idx: List[Tuple[Optional[Union[str, MudStyle, None]], str]]):
        out = MudText()
        for i, t in enumerate(idx):
            s = [Span(0, 1, t[0])]
            out.append_text(MudText(text=t[1], spans=s))
        return out

    def style_at_index(self, offset: int) -> MudStyle:
        if offset < 0:
            offset = len(self) + offset
        style = MudStyle()
        for start, end, span_style in self._spans:
            if end > offset >= start:
                style = style + span_style
        return style

    def disassemble_bits(self) -> List[Tuple[Optional[Union[str, MudStyle, None]], str]]:
        idx = list()
        for i, c in enumerate(self.plain):
            idx.append((self.style_at_index(i), c))
        return idx

    def serialize(self) -> dict:
        def ser_style(style):
            if isinstance(style, str):
                style = MudStyle.parse(style)
            if not isinstance(style, MudStyle):
                style = MudStyle.upgrade(style)
            return style.serialize()

        def ser_span(span):
            if not span.style:
                return None
            return {
                'start': span.start,
                'end': span.end,
                'style': ser_style(span.style)
            }

        out = {
            "text": self.plain
        }

        if self.style:
            out['style'] = ser_style(self.style)

        out_spans = [s for span in self.spans if (s := ser_span(span))]

        if out_spans:
            out['spans'] = out_spans

        return out

    @classmethod
    def deserialize(cls, data) -> "MudText":
        text = data.get("text", None)
        if text is None:
            return cls("")
        style = data.get("style", None)
        if style:
            style = MudStyle(**style)

        spans = data.get("spans", None)

        if spans:
            spans = [Span(s['start'], s['end'], MudStyle(**s['style'])) for s in spans]

        return cls(text=text, style=style, spans=spans)

    def squish(self) -> "MudText":
        """
        Removes leading and trailing whitespace, and coerces all internal whitespace sequences
        into at most a single space. Returns the results.
        """
        out = list()
        matches = _RE_SQUISH.finditer(self.plain)
        for match in matches:
            out.append(self[match.start():match.end()])
        return MudText(" ").join(out)

    def squish_spaces(self) -> "MudText":
        """
        Like squish, but retains newlines and tabs. Just squishes spaces.
        """
        out = list()
        matches = _RE_NOTSPACE.finditer(self.plain)
        for match in matches:
            out.append(self[match.start():match.end()])
        return MudText(" ").join(out)

    @classmethod
    def upgrade(cls, text: OLD_TEXT) -> "MudText":
        if isinstance(text, cls):
            return text
        elif isinstance(text, str):
            return MudText(text)
        elif isinstance(text, OLD_TEXT):
            return cls(text=text.plain, style=text.style, spans=text.spans)
        else:
            raise ValueError("Must be a string or Text instance!")
