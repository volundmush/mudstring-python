# this is largely adapted from PennMUSH's ansi.h and related files.
import random
import re
import html
import copy

from typing import Union, Optional, List, Tuple, NamedTuple
from . markup import Markup, MXPMarkup, ColorMarkup


class TextError(Exception):
    pass


class Span(NamedTuple):
    """A marked up region in some text."""

    start: int
    """Span start index."""
    end: int
    """Span end index."""
    style: Optional[Markup]
    """Style associated with the span."""

    def __repr__(self) -> str:
        return f"Span({self.start}, {self.end}, {str(self.style)!r})"

    def __bool__(self) -> bool:
        return self.end > self.start

    def split(self, offset: int) -> Tuple["Span", Optional["Span"]]:
        """Split a span in to 2 from a given offset."""

        if offset < self.start:
            return self, None
        if offset >= self.end:
            return self, None

        start, end, style = self
        span1 = Span(start, min(end, offset), style)
        span2 = Span(span1.end, end, style)
        return span1, span2

    def move(self, offset: int) -> "Span":
        """Move start and end by a given offset.
        Args:
            offset (int): Number of characters to add to start and end.
        Returns:
            TextSpan: A new TextSpan with adjusted position.
        """
        start, end, style = self
        return Span(start + offset, end + offset, style)

    def right_crop(self, offset: int) -> "Span":
        """Crop the span at the given offset.
        Args:
            offset (int): A value between start and end.
        Returns:
            Span: A new (possibly smaller) span.
        """
        start, end, style = self
        if offset >= end:
            return self
        return Span(start, min(offset, end), style)


class Text:
    re_format = re.compile(
        r"(?i)(?P<just>(?P<fill>.)?(?P<align>\<|\>|\=|\^))?(?P<sign>\+|\-| )?(?P<alt>\#)?"
        r"(?P<zero>0)?(?P<width>\d+)?(?P<grouping>\_|\,)?(?:\.(?P<precision>\d+))?"
        r"(?P<type>b|c|d|e|E|f|F|g|G|n|o|s|x|X|%)?"
    )
    codecs = {}

    __slots__ = ["plain", "spans"]

    @classmethod
    def install_codec(cls, name: str, encoder: callable, decoder: callable):
        cls.codecs[name] = {"encoder": encoder, "decoder": decoder}

    def __init__(self, src: str = "", spans: Optional[List[Span]] = None):
        self.plain = src
        self.spans = spans

    def __len__(self):
        return len(self.plain)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.plain == other
        if isinstance(other, Text):
            return self.plain == other.plain
        return False

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

    def render(self, ansi: bool = False, xterm256: bool = False, mxp: bool = False, downgrade: bool = True):
        """
        Does all the hard work of turning this Text into ANSI fit for display over telnet.

        Args:
            ansi (bool): Whether ANSI is supported. Will not output ANSI if not.
            xterm256 (bool): Whether to support xterm256 colors. This will force ANSI on if true.
            mxp (bool): Support Pueblo/MXP HTML-over-telnet rendering.
            downgrade (bool): If the client supports ansi but not xterm256, this allows a downgrade to 16-color
                codes by nearest match. It can be ugly so be careful.

        Returns:
            ansi-encoded string (str)

        """
        if xterm256:
            ansi = True
        if not (ansi or xterm256 or mxp):
            return self.plain
        # well at this point it appears we are going to be returning ANSI.

        output = ""
        tag_stack = list()
        ansi_stack = list()
        mxp_stack = list()
        cur = None
        cur_ansi = None
        cur_mxp = None

        for i, span in enumerate(self.spans):
            if isinstance(span.style, Markup):
                if cur:
                    # we are already inside of a markup!
                    if span.style is cur:
                        pass
                    else:
                        # moving to a different markup.
                        if span.style.parent is cur:
                            # we moved into a child.
                            if isinstance(span.style, MXPMarkup) and mxp:
                                output += span.style.enter_html()
                                mxp_stack.append(span.style)
                            elif isinstance(span.style, ColorMarkup) and ansi:
                                ansi_stack.append(span.style)
                                output += span.style.transition(cur_ansi, xterm256=xterm256, downgrade=downgrade)
                            tag_stack.append(span.style)
                        else:
                            # We left a tag and are moving into another kind of tag. It might be a parent, an ancestor,
                            # or completely unrelated. Let's find out which, first!
                            ancestors = cur.ancestors(reversed=True)
                            idx = None

                            if span.style in tag_stack:
                                # We need to close out of the ancestors we no longer have. A slice accomplishes that.
                                tags_we_left = ancestors[tag_stack.index(span.style):]
                                ansi_we_left = [t for t in tags_we_left if isinstance(t, ColorMarkup)]
                                mxp_we_left = [t for t in tags_we_left if isinstance(t, MXPMarkup)]
                                for _ in range(len(tags_we_left)-1):
                                    tag_stack.pop(-1)

                                # now that we know what to leave, let's leave them.
                                if len(ansi_we_left) == len(ansi_stack):
                                    # we left all ANSI.
                                    cur_ansi = None
                                    ansi_stack.clear()
                                    output += ColorMarkup.ANSI_RAW_NORMAL
                                else:
                                    # we left almost all ANSI...
                                    for _ in range(len(ansi_we_left) - 1):
                                        ansi_stack.pop(-1)
                                    cur_ansi = ansi_stack[-1]
                                    output += ColorMarkup.ANSI_RAW_NORMAL
                                    output += cur_ansi.render(xterm256=xterm256, downgrade=downgrade)

                                if len(mxp_we_left) == len(mxp_stack):
                                    # we left all MXP.
                                    cur_mxp = None
                                    mxp_stack.clear()
                                else:
                                    for i in range(len(mxp_we_left) - 1):
                                        mxp_stack.pop(-1)
                                    cur_mxp = mxp_stack[-1]
                                for mx in reversed(mxp_we_left):
                                    output += mx.exit_html()

                            else:
                                # it's not an ancestor at all, so close out of everything and rebuild.
                                if ansi_stack:
                                    output += ColorMarkup.ANSI_RAW_NORMAL
                                    ansi_stack.clear()
                                    cur_ansi = None
                                if mxp_stack:
                                    for mx in reversed(mxp_stack):
                                        output += mx.exit_html()
                                    mxp_stack.clear()
                                    cur_mxp = None
                                tag_stack.clear()

                                # Now to enter the new tag...

                                for ancestor in span.style.ancestors(reversed=True):
                                    if isinstance(ancestor, MXPMarkup) and mxp:
                                        mxp_stack.append(ancestor)
                                    elif isinstance(ancestor, ColorMarkup) and ansi:
                                        ansi_stack.append(ancestor)

                                if isinstance(span.style, MXPMarkup) and mxp:
                                    mxp_stack.append(span.style)
                                elif isinstance(span.style, ColorMarkup) and ansi:
                                    ansi_stack.append(span.style)

                                for an in mxp_stack:
                                    output += an.enter_html()
                                    cur_mxp = an

                                if ansi_stack:
                                    cur_ansi = ansi_stack[-1]
                                    output += cur_ansi.render(xterm256=xterm256, downgrade=downgrade)

                        cur = span.style
                else:
                    # We are not inside of a markup tag. Well, that changes now.
                    cur = span.style
                    for ancestor in span.style.ancestors(reversed=True):
                        if isinstance(ancestor, MXPMarkup) and mxp:
                            mxp_stack.append(ancestor)
                        elif isinstance(ancestor, ColorMarkup) and ansi:
                            ansi_stack.append(ancestor)
                        tag_stack.append(ancestor)

                    if isinstance(span.style, MXPMarkup) and mxp:
                        mxp_stack.append(cur)
                    elif isinstance(span.style, ColorMarkup) and ansi:
                        ansi_stack.append(cur)

                    for an in mxp_stack:
                        output += an.enter_html()
                        cur_mxp = an

                    if ansi_stack:
                        cur_ansi = ansi_stack[-1]
                        output += cur_ansi.render(xterm256=xterm256, downgrade=downgrade)

            else:
                # we are moving into a None markup...
                if cur:
                    if ansi_stack:
                        output += ColorMarkup.ANSI_RAW_NORMAL
                        ansi_stack.clear()
                        cur_ansi = None

                    if mxp_stack:
                        for mx in reversed(mxp_stack):
                            output += mx.exit_html()
                        mxp_stack.clear()
                        cur_mxp = None

                    cur = None
                else:
                    # from no markup to no markup. Just append the character.
                    pass

            # Then append this span's text
            output += html.escape(self.plain[span.start:span.end]) if mxp else self.plain[span.start:span.end]

        # Finalize and exit all remaining tags.
        if ansi_stack:
            output += ColorMarkup.ANSI_RAW_NORMAL

        if mxp_stack:
            for mx in reversed(mxp_stack):
                output += mx.exit_html()

        return output

    @classmethod
    def from_plain(cls, src: str = ""):
        return cls(src=src, spans=[Span(0, len(src), None)])
