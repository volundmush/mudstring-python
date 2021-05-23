from rich import text
from rich.text import Span, Segment
from typing import List, Set, Union, Dict, Tuple, Optional
from . style import MudStyle, OLD_STYLE
from rich.control import strip_control_codes
import random

OLD_TEXT = text.Text


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

    def ljust(self, width, fillchar=' '):
        return self.__class__(self.plain.ljust(width, fillchar).replace(self.plain, self.encode()))

    def rjust(self, width, fillchar=' '):
        return self.__class__(self.plain.ljust(width, fillchar).replace(self.plain, self.encode()))

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

    @classmethod
    def assemble_bits(cls, idx: List[Tuple[Optional[Union[str, MudStyle, None]], str]]):
        out = MudText()
        for i, t in enumerate(idx):
            s = [Span(0, 1, t[0])]
            out.append_text(MudText(text=t[1], spans=s))
        return out

    def style_at_index(self, offset: int) -> MudStyle:
        """Get the style of a character at give offset.
        Args:
            offset (int): Offset in to text (negative indexing supported)
        Returns:
            Style: A Style instance.
        """
        # TODO: This is a little inefficient, it is only used by full justify
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