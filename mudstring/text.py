# this is largely adapted from PennMUSH's ansi.h and related files.
import random
import re
import html
import copy

from typing import Union, Optional, List, Tuple, NamedTuple


class Text:
    re_format = re.compile(
        r"(?i)(?P<just>(?P<fill>.)?(?P<align>\<|\>|\=|\^))?(?P<sign>\+|\-| )?(?P<alt>\#)?"
        r"(?P<zero>0)?(?P<width>\d+)?(?P<grouping>\_|\,)?(?:\.(?P<precision>\d+))?"
        r"(?P<type>b|c|d|e|E|f|F|g|G|n|o|s|x|X|%)?"
    )
    codecs = {}

    def disassemble(self) -> List[Tuple[Optional[Markup], str]]:
        idx = list()
        for i, span in enumerate(self.spans):
            for c in self.plain[span.start:span.end]:
                idx.append((span.style, c))
        return idx

    @classmethod
    def assemble(cls, idx: List[Tuple[Optional[Markup], str]]):
        start = 0
        style = None
        spans = list()
        txt = ""
        for i, t in enumerate(idx):
            if i == 0:
                style = t[0]

            if (style is None and t[0] is None) or t[0] == style:
                pass
            else:
                spans.append(Span(start, i, style))
                style = t[0]
                start = i
            txt += t[1]
        if not spans:
            spans.append(Span(0, len(txt), style))
        return cls(src=txt, spans=spans)

    def __getitem__(self, slice: Union[int, slice]) -> "Text":
        # TODO: this is incredibly inefficient. need a better approach.

        # first, generate a list of tuples of (style, char)
        idx = self.disassemble()

        # now, slice the list.
        if isinstance(slice, int):
            tup = idx[slice]
            span = Span(0, 0, tup[0])
            return self.__class__(src=tup[1], spans=[span])
        else:
            return self.__class__.assemble(idx.__getitem__(slice))

    def __str__(self):
        return self.plain

    def __format__(self, format_spec):
        return self.plain.__format__(format_spec)

    def __bool__(self):
        return bool(self.plain)

    def __mul__(self, other):
        if not isinstance(other, int):
            return self
        if other <= 0:
            return Text()
        if other == 1:
            return self.clone()
        if other > 1:
            new_plain = self.plain * other
            new_spans = list()
            l = len(self.plain)
            for i in range(other):
                new_spans += [s.move(l*i) for s in self.spans]
            return self.__class__(src=new_plain, spans=new_spans)

    def __rmul__(self, other):
        if not isinstance(other, int):
            return self
        return self * other

    def __add__(self, other):
        if not len(other):
            return self.clone()
        if not isinstance(other, Text):
            other = self.__class__.from_plain(other)
        n = self.clone()
        n += other
        return n

    def __iadd__(self, other):
        if not len(other):
            return self
        if isinstance(other, str):
            other = self.__class__.from_plain(other)
        if isinstance(other, Text):
            l = len(self.plain)
            self.plain += other.plain
            self.spans += [s.move(l) for s in other.spans]
            return self
        else:
            raise ValueError("Unsupported Operation Iadd for this type")

    def __radd__(self, other):
        return self.__class__.from_plain(other) + self

    def __repr__(self):
        return f"<Text({repr(self.plain)}, Spans={repr(self.spans)})>"

    def clone(self):
        return self.__class__(src=self.plain, spans=list(self.spans))

    def split(self, sep: str = ' ', maxsplit: int = None):
        tuples = list()
        if maxsplit is None or maxsplit == 0:
            limit = -1
        else:
            limit = maxsplit
        count = 0
        cur = list()
        idx = self.disassemble()
        for i, t in enumerate(idx):
            if t[1] == sep:
                if cur:
                    tuples.append(cur)
                    count += 1
                    cur = list()
                    if limit == count:
                        cur.extend(idx[i:])
                        break
            else:
                cur.append(t)
        if cur:
            tuples.append(cur)
        return [self.__class__.assemble(tup) for tup in tuples]

    def join(self, iterable):
        out_lists = list()
        separator = self.disassemble()
        for i, oth in enumerate(iterable):
            if oth:
                if isinstance(oth, Text):
                    out_lists.append(oth.disassemble())
                elif isinstance(oth, str):
                    out_lists.append([(None, c) for c in list(oth)])

        total = len(out_lists)
        out_tuples = list()
        for i, l in enumerate(out_lists):
            out_tuples.extend(l)
            if i+1 < total:
                out_tuples.extend(separator)
        return self.__class__.assemble(idx=out_tuples)

    def capitalize(self):
        return self.__class__(src=self.plain.capitalize(), spans=list(self.spans))

    def count(self, *args, **kwargs):
        return self.plain.count(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        return self.plain.startswith(*args, **kwargs)

    def endswith(self, *args, **kwargs):
        return self.plain.endswith(*args, **kwargs)

    def center(self, width, fillchar=' '):
        changed = self.plain.center(width, fillchar)
        start = changed.find(self.plain)
        lside = changed[:start]
        rside = changed[len(lside)+len(self.plain):]
        idx = self.disassemble()
        new_idx = list()
        for c in lside:
            new_idx.append((None, c))
        new_idx.extend(idx)
        for c in rside:
            new_idx.append((None, c))
        return self.__class__.assemble(new_idx)

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

    def ljust(self, width, fillchar=' '):
        return self.__class__(self.plain.ljust(width, fillchar).replace(self.plain, self.encode()))

    def rjust(self, width, fillchar=' '):
        return self.__class__(self.plain.ljust(width, fillchar).replace(self.plain, self.encode()))

    def lstrip(self, chars: str = None):
        lstripped = self.plain.lstrip(chars)
        strip_count = len(self.plain) - len(lstripped)
        return self[strip_count:]

    def strip(self, chars: str = ' '):
        out_map = self.disassemble()
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
        return self.__class__.assemble(out_map)

    def replace(self, old: str, new: str, count=None):
        if not (indexes := self.find_all(old)):
            return self.clone()
        if count and count > 0:
            indexes = indexes[:count]
        old_len = len(old)
        new_len = len(new)
        other = self.clone()
        markup_idx_map = self.disassemble()
        other_map = other.disassemble()

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

        return self.__class__.assemble(other_map)

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
        idx = self.disassemble()
        random.shuffle(idx)
        return self.__class__.assemble(idx)