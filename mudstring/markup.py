import html
from . colors import COLORS, FG_DOWNGRADE, BG_DOWNGRADE
from colored.hex import HEX
from typing import Dict


class _CODES:
    BEEP_CHAR = '\a'
    ESC_CHAR = '\x1B'
    ANSI_START = ESC_CHAR + '['
    ANSI_RAW_NORMAL = '\x1B[0m'

    ANSI_FORMAT_NONE = 0
    ANSI_FORMAT_HILITE = 1
    ANSI_FORMAT_16COLOR = 2
    ANSI_FORMAT_XTERM256 = 3
    ANSI_FORMAT_HTML = 4

    MARKUP_COLOR = 'c'
    MARKUP_COLOR_STR = "c"
    MARKUP_HTML = 'p'
    MARKUP_HTML_STR = "p"
    MARKUP_OLDANSI = 'o'
    MARKUP_OLDANSI_STR = "o"

    MARKUP_WS = 'w'
    MARKUP_WS_ALT = 'W'
    MARKUP_WS_ALT_END = 'M'

    ANSI_BEGIN = '\x1B['
    ANSI_FINISH = 'm'
    CBIT_HILITE = 1
    CBIT_INVERT = 2
    CBIT_FLASH = 4
    CBIT_UNDERSCORE = 8

    COL_NORMAL = 0
    COL_HILITE = 1
    COL_UNDERSCORE = 4
    COL_FLASH = 5
    COL_INVERT = 7

    COL_BLACK = 30
    COL_RED = 31
    COL_GREEN = 32
    COL_YELLOW = 33
    COL_BLUE = 34
    COL_MAGENTA = 35
    COL_CYAN = 36
    COL_WHITE = 37

    CS_NONE = 0
    CS_HEX = 1
    CS_16 = 2
    CS_256 = 3
    CS_RGBHEX = 4
    CS_RGB = 5
    CS_NAME = 6
    CS_XNAME = 7


STATES = {
    '#': "hex",
    '<': "rgb",
    '+': "name"
}


CBIT_MAP = {
    _CODES.CBIT_HILITE: '1',
    _CODES.CBIT_UNDERSCORE: '4',
    _CODES.CBIT_INVERT: '7',
    _CODES.CBIT_FLASH: '5'
}


STYLES = {
    'hilite': _CODES.COL_HILITE,
    'underscore': _CODES.COL_UNDERSCORE,
    'flash': _CODES.COL_FLASH,
    'invert': _CODES.COL_INVERT
}


class Markup:

    __slots__ = ["children", "parent"]

    def __init__(self, parent=None):
        self.children = list()
        self.parent = parent
        if self.parent:
            self.parent.children.append(self)

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
            while (parent := parent.parent):
                out.append(parent)
        if reversed:
            out.reverse()
        return out

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class ColorMarkup(Markup):
    ANSI_RAW_NORMAL = _CODES.ANSI_RAW_NORMAL

    __slots__ = ["bits", "off_bits", "fg_mode", "fg_clear", "fg_color", "bg_mode", "bg_clear", "bg_color", "reset"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bits = 0
        self.off_bits = 0
        self.fg_mode = None
        self.fg_clear = False
        self.fg_color = None
        self.bg_mode = None
        self.bg_clear = False
        self.bg_color = None
        self.reset = False

    def do_reset(self):
        self.bits = 0
        self.off_bits = 0
        self.fg_mode = None
        self.fg_clear = False
        self.fg_color = None
        self.bg_mode = None
        self.bg_clear = False
        self.bg_color = None
        self.reset = True

    def __repr__(self):
        return f"<{self.__class__.__name__}: STYLE: {self.bits}/{self.off_bits} FG: {self.fg_mode}/{self.fg_color}/{self.fg_clear} BG: {self.bg_mode}/{self.bg_color}/{self.bg_clear} RESET: {self.reset}>"

    def remove_style(self, name: str):
        if (val := STYLES.get(name, None)):
            self.off_bits |= val
            self.bits &= ~val
            self.reset = False

    def apply_style(self, name: str):
        if (val := STYLES.get(name, None)):
            self.bits |= val
            self.off_bits &= ~val
            self.reset = False

    def set_ansi_fg(self, color: int):
        if color is None:
            self.fg_clear = True
            self.fg_color = None
            self.fg_mode = None
        else:
            self.fg_mode = 0
            self.fg_color = color
            self.fg_clear = False
        self.reset = False

    def set_xterm_fg(self, color: int):
        if color is None:
            self.fg_clear = True
            self.fg_color = None
            self.fg_mode = None
        else:
            self.fg_mode = 1
            self.fg_color = color
            self.fg_clear = False
        self.reset = False

    def set_ansi_bg(self, color: int):
        if color is None:
            self.bg_clear = True
            self.bg_color = None
            self.bg_mode = None
        else:
            self.bg_mode = 0
            self.bg_color = color
            self.bg_clear = False
        self.reset = False

    def set_xterm_bg(self, color: int):
        if color is None:
            self.bg_clear = True
            self.bg_color = None
            self.bg_mode = None
        else:
            self.bg_mode = 1
            self.bg_color = color
            self.bg_clear = False
        self.reset = False

    def inherit_ansi(self):
        for a in self.ancestors():
            if hasattr(a, "bits"):
                for attr in ("bits", "off_bits", "fg_mode", "fg_clear", "fg_color", "bg_mode", "bg_clear", "bg_color", "reset"):
                    setattr(self, attr, getattr(a, attr))
                return

    def styles(self, bits: int):
        return [v for k, v in CBIT_MAP.items() if bits & k]

    def render(self, xterm256: bool = True, downgrade: bool = True):
        """
        This method returns the ANSI escape sequence representing this object.
        Use it to 'just start printing ansi' in this object's style.

        Args:
            xterm256 (bool): Whether xterm is enabled. If not, Xterm colors may be downgraded to 16-color.
            downgrade (bool): if not xterm256, whether to downgrade or just ignore colors.

        Returns:
            ansi (str): A raw string containing ANSI escape codes. It might be empty.
        """
        if self.reset:
            return _CODES.ANSI_RAW_NORMAL

        reset = False
        codes = list()
        out_bits = self.bits

        if self.fg_clear or self.bg_clear:
            reset = True
            # a 'd' letter sets fg clear. Colors can only be replaced, so to 'clear' colors we must ANSI reset.

        if reset:
            codes.append('0')
        # retrieve any codes for invert, hilite, underscore, etc, and append.

        fg_codes = ''
        if not self.fg_clear:
            # if fg_clear, fg_mode should be None...
            if self.fg_mode == 0:
                fg_codes = str(self.fg_color)
            if self.fg_mode == 1:
                if xterm256:
                    fg_codes = f"38;5;{self.fg_color}"
                else:
                    if downgrade:
                        hilite, code = FG_DOWNGRADE[self.fg_color]
                        fg_codes = str(code)
                        if hilite:
                            out_bits |= _CODES.CBIT_HILITE

        bg_codes = ''
        if not self.bg_clear:
            # if fg_clear, fg_mode should be None...
            if self.bg_mode == 0:
                bg_codes = str(self.bg_color)
            if self.bg_mode == 1:
                if xterm256:
                    bg_codes = f"48;5;{self.bg_color}"
                else:
                    if downgrade:
                        hilite, code = BG_DOWNGRADE[self.bg_color]
                        bg_codes = str(code)
                        if hilite:
                            out_bits |= _CODES.CBIT_HILITE

        # all codes that need to be added are now decided.
        if out_bits:
            codes.extend(self.styles(out_bits))
        if fg_codes:
            codes.append(fg_codes)
        if bg_codes:
            codes.append(bg_codes)
        final_codes = ';'.join(codes)
        if final_codes:
            return f"{_CODES.ANSI_START}{final_codes}m"
        else:
            return ''

    def transition(self, to, xterm256: bool = True, downgrade: bool = True):
        """
        This method returns an ANSI escape sequence representing the transition of the ANSI state of itself,
        to the ANSI state of 'to'.

        Args:
            to (AnsiData): The object being transitioned to.
            xterm256 (bool): Whether xterm is enabled. If not, Xterm colors may be downgraded to 16-color.
            downgrade (bool): if not xterm256, whether to downgrade or just ignore colors.

        Returns:
            ansi (str): A raw string containing ANSI escape codes. It might be empty.
        """
        # Whether an ANSI Reset will be necessary. Many things might force this necessity.
        reset = False

        if self.bits & to.off_bits:
            # Hilite, Invert, underscore, strikethrough, etc, cannot be simply 'turned off' - the ANSI state must be
            # cleanly reset instead.
            reset = True
        remaining = self.bits ^ to.off_bits

        out_bits = to.bits | remaining

        # codes contains a temporary list of the ANSI codes which will be joined by ; eventually.
        # this is a list of strings.
        codes = list()

        if to.fg_clear or to.bg_clear:
            reset = True
            # a 'd' letter sets fg clear. Colors can only be replaced, so to 'clear' colors we must ANSI reset.

        if reset:
            codes.append('0')
        # retrieve any codes for invert, hilite, underscore, etc, and append.

        # Past this point, we can only apply color codes.
        fg_codes = ''
        if not to.fg_clear:
            # if fg_clear, fg_mode should be None...
            if to.fg_mode == 0:
                fg_codes = str(to.fg_color)
            if to.fg_mode == 1:
                if xterm256:
                    fg_codes = f"38;5;{to.fg_color}"
                else:
                    if downgrade:
                        hilite, code = FG_DOWNGRADE[to.fg_color]
                        fg_codes = str(code)
                        if hilite:
                            out_bits |= _CODES.CBIT_HILITE

        bg_codes = ''
        if not to.bg_clear:
            # if fg_clear, fg_mode should be None...
            if to.bg_mode == 0:
                bg_codes = str(to.bg_color)
            if to.bg_mode == 1:
                if xterm256:
                    bg_codes = f"48;5;{to.bg_color}"
                else:
                    if downgrade:
                        hilite, code = BG_DOWNGRADE[to.bg_color]
                        bg_codes = str(code)
                        if hilite:
                            out_bits |= _CODES.CBIT_HILITE

        # all codes that need to be added are now decided.
        if out_bits:
            codes.extend(to.styles(out_bits))
        if fg_codes:
            codes.append(fg_codes)
        if bg_codes:
            codes.append(bg_codes)
        final_codes = ';'.join(codes)
        if final_codes:
            return f"{_CODES.ANSI_START}{final_codes}m"
        else:
            return ''


class MXPMarkup(Markup):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tag = ''
        self.attributes = dict()

    def __repr__(self):
        if self.attributes:
            attr = ' '.join(f'{k}="{v}"' for k, v in self.attributes.items())
            return f"<{self.__class__.__name__}: {self.tag} {attr}>"
        else:
            return f"<{self.__class__.__name__}: {self.tag}>"

    def enter_html(self):
        if self.attributes:
            attr = ' '.join(f'{k}="{html.escape(v)}"' for k, v in self.attributes.items())
            return f"{_CODES.ANSI_START}4z<{self.tag} {attr}>"
        return f"{_CODES.ANSI_START}4z<{self.tag}>"

    def exit_html(self):
        return f"{_CODES.ANSI_START}4z</{self.tag}>"

    def setup(self, tag: str, attr: Dict[str, str]):
        self.tag = tag
        self.attributes = attr
